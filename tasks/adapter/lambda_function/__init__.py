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

from ..shared import Error


def make_lambda_handler():
    def tasks_lambda_handler(event, context):
        # Here the event is whatever you pass as the JSON when executing the stepfunctions state machine
        uid = context.aws_request_id
        delay_ms = int((os.environ.get("DELAY_MS", "0")))
        safety_multiple = float(os.environ.get("SAFETY_MULTIPLE", "1.4"))
        safety_delay_ms = int((os.environ.get("SAFETY_DELAY_MS", "0")))
        print(event, context, uid, delay_ms, safety_multiple, safety_delay_ms)
        workflow_id = event["workflow_id"]

        next_task, state = tasks.driver.get_next_task(workflow_id)
        module, obj = state["handler"].split(":")
        m = importlib.import_module(module)
        handler_function = getattr(m, obj)
        # This algorithm will always try and run at least one task
        longest_task_ms = 0.0

        def patch_state(data):
            # Save to store
            tasks.driver.patch_state(workflow_id, data)
            # And update locally
            state.update(data)

        for i in range(next_task, state["num_tasks"] + 1):
            time.sleep(delay_ms / 1000.0)
            begun = False
            ended = False
            now = time.time()
            begun_at = datetime.datetime.now()

            def register_begin(task_state):
                nonlocal begun
                begun = True
                tasks.driver.begin_task(
                    uid, workflow_id, state["num_tasks"], i, task_state, begun_at
                )

            def register_end(patch_task_state=None):
                nonlocal ended
                ended = True
                ended_at = datetime.datetime.now()
                tasks.driver.end_task(
                    uid, workflow_id, state["num_tasks"], i, patch_task_state, ended_at
                )

            handler_function(i, state, patch_state, register_begin, register_end)

            if not begun:
                print(
                    f'WARNING: register_begin() was not called by {repr(state["handler"])} for task number {i}.'
                )
                tasks.driver.begin_task(
                    uid, workflow_id, state["num_tasks"], i, begun_at=begun_at
                )
            if not ended:
                print(
                    f'WARNING: register_end() was not called by {repr(state["handler"])} for task number {i}.'
                )
                ended_at = datetime.datetime.now()
                tasks.driver.end_task(
                    uid, workflow_id, state["num_tasks"], i, ended_at=ended_at
                )

            elapsed_ms: float = (time.time() - now) * 1000
            if elapsed_ms > longest_task_ms:
                longest_task_ms = elapsed_ms

            remaining_ms = context.get_remaining_time_in_millis()
            needed_ms = (longest_task_ms * safety_multiple) + safety_delay_ms + delay_ms
            if remaining_ms < needed_ms:
                raise Error(
                    f"Out of time to run the next task. Need {needed_ms} ms but only have {remaining_ms}"
                )

        print("Longest task (ms):", longest_task_ms)
        tasks.driver.end_workflow(uid, workflow_id)
        # This becomes the output of the state machine
        event["success"] = True
        return event

    return tasks_lambda_handler
