import base64
import datetime
import importlib
import os
import time

encoded_environment = os.environ.get("ENCODED_ENVIRONMENT", "")
if encoded_environment:
    for pair in encoded_environment.split(","):
        if pair:
            # print(pair)
            pairs = pair.split("|")
            # print(pairs)
            if len(pairs) != 2:
                print(
                    f'Warning: The encoded environment pair {repr(pair)} is ignored becuase there is not exaclty one "|" character. Please encode it properly'
                )
            else:
                key = pairs[0]
                value = pairs[1]
                if key[0] == "$":
                    key = base64.b64decode(key).decode("utf8")
                if value[0] == "$":
                    value = base64.b64decode(value).decode("utf8")
                if key in os.environ:
                    print(
                        f"Warning: Key {repr(key)} already exists in environ with value {repr(os.environ[key])}. Replacing it with {repr(value)}."
                    )
                # print(key, value)
                os.environ[key] = value
# print(os.environ)


# Must come after the environment is set up
import tasks.driver
from tasks.adapter.shared import make_task, Abort, RenderableTaskAbort, OutOfTime


def make_lambda_handler():
    def tasks_lambda_handler(event, context):
        # Here the event is whatever you pass as the JSON when executing the stepfunctions state machine
        uid = context.aws_request_id
        delay_ms = int((os.environ.get("DELAY_MS", "0")))
        safety_multiple = float(os.environ.get("SAFETY_MULTIPLE", "1.4"))
        safety_delay_ms = int((os.environ.get("SAFETY_DELAY_MS", "0")))
        print(event, context, uid, delay_ms, safety_multiple, safety_delay_ms)
        workflow_id = event["workflow_id"]
        next_task, workflow_state, task_state = tasks.driver.get_next_task(workflow_id)

        if "abort" in workflow_state and str(workflow_state["abort"]).lower() in [
            "1",
            "true",
        ]:
            Abort("Workflow aborted via abort key in workflow state")

        if task_state is not None and "end" in task_state:
            # It must have already been run, and failed. Let's reset it so it can run again.
            next_task = next_task - 1
            # When begin task is called below, it will overwrite the old data

        module, obj = workflow_state["handler"].split(":")
        m = importlib.import_module(module)
        handler_function = getattr(m, obj)
        # This algorithm will always try and run at least one task
        longest_task_ms = 0.0

        def patch_workflow_state(data):
            # Save to store
            tasks.driver.patch_state(workflow_id, data)
            # And update locally
            workflow_state.update(data)

        for number in range(next_task, workflow_state["num_tasks"] + 1):
            time.sleep(delay_ms / 1000.0)
            task = make_task(
                uid,
                workflow_id=workflow_id,
                workflow_state=workflow_state,
                patch_workflow_state=patch_workflow_state,
                number=number,
            )

            now = time.time()

            try:
                handler_function(task)
            except Abort as a:
                if isinstance(a, RenderableTaskAbort):
                    task.correctly_escaped_html_status_message = a.render()
                task.end_state_patches["failed"] = 1
                tasks.driver.end_task(
                    uid,
                    workflow_id,
                    workflow_state["num_tasks"],
                    number,
                    str(task.correctly_escaped_html_status_message),
                    task.end_state_patches,
                    datetime.datetime.now(),
                )
                raise Abort(str(a))
            else:
                tasks.driver.end_task(
                    uid,
                    workflow_id,
                    workflow_state["num_tasks"],
                    number,
                    str(task.correctly_escaped_html_status_message),
                    task.end_state_patches,
                    datetime.datetime.now(),
                )
            if not task._begun:
                raise Exception(
                    f'task.begin() was not called by {repr(workflow_state["handler"])} for task number {number}.'
                )
            elapsed_ms: float = (time.time() - now) * 1000
            if elapsed_ms > longest_task_ms:
                longest_task_ms = elapsed_ms

            remaining_ms = context.get_remaining_time_in_millis()
            needed_ms = (longest_task_ms * safety_multiple) + safety_delay_ms + delay_ms
            if remaining_ms < needed_ms:
                raise OutOfTime(
                    f"Out of time to run the next task. Need {needed_ms} ms but only have {remaining_ms}"
                )

        print("Longest task (ms):", longest_task_ms)
        tasks.driver.end_workflow(uid, workflow_id)
        # This becomes the output of the state machine
        event["success"] = True
        return event

    return tasks_lambda_handler
