import base64
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
                    f'Warning: The encoded environment pair {repr(pair)} is ignored becuase there are too many "|" characters. Please encode it properly'
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


def make_lambda_handler(app_tasks):
    def tasks_lambda_handler(event, context):
        # Here the event is whatever you pass as the JSON when executing the stepfunctions state machine
        uid = context.aws_request_id
        delay_ms = int((os.environ.get("DELAY_MS", "0")))
        safety_multiple = float(os.environ.get("SAFETY_MULTIPLE", "1.4"))
        safety_delay_ms = int((os.environ.get("SAFETY_DELAY_MS", "0")))
        print(event, context, uid, delay_ms, safety_multiple, safety_delay_ms)
        workflow_id = event["workflow_id"]

        next_task, num_tasks, handler = tasks.driver.get_next_task(workflow_id)
        handler_function = getattr(app_tasks, handler)
        # This algorithm will always try and run at least one task
        longest_task_ms = 0.0

        for i in range(next_task, num_tasks + 1):
            time.sleep(delay_ms / 1000.0)

            def handler_begin_task():
                return tasks.driver.begin_task(uid, workflow_id, num_tasks, i)

            def handler_end_task():
                return tasks.driver.end_task(uid, workflow_id, num_tasks, i)

            now = time.time()
            handler_function(next_task, num_tasks, handler_begin_task, handler_end_task)
            elapsed_ms = (time.time() - now) * 1000
            if elapsed_ms > longest_task_ms:
                longest_task_ms = elapsed_ms
            remaining_ms = context.get_remaining_time_in_millis()
            needed_ms = (longest_task_ms * safety_multiple) + safety_delay_ms + delay_ms
            if remaining_ms < needed_ms:
                raise Error(
                    f"Out of time to run the next task. Need {needed_ms} ms but only have {remaining_ms}"
                )

        tasks.driver.end_workflow(uid, workflow_id)
        # This becomes the output of the state machine
        event["success"] = True
        return event

    return tasks_lambda_handler


_handler: list = []


def lambda_handler(event, context):
    global _handler
    if len(_handler) == 0:
        import app.tasks

        _handler.append(make_lambda_handler(app.tasks))
    return _handler[0](event, context)
