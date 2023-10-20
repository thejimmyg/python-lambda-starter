import os
import time

import app.tasks
from driver.tasks.auto import begin_task, end_task, end_workflow, get_next_task

from .shared import Error


def lambda_handler(event, context):
    # Here the event is whatever you pass as the JSON when executing the stepfunctions state machine
    uid = context.aws_request_id
    delay_ms = int((os.environ.get("DELAY_MS", "0")))
    safety_multiple = float(os.environ.get("SAFETY_MULTIPLE", "1.4"))
    safety_delay_ms = int((os.environ.get("SAFETY_DELAY_MS", "0")))
    print(event, context, uid, delay_ms, safety_multiple, safety_delay_ms)
    workflow_id = event["workflow_id"]

    next_task, tasks, handler = get_next_task(workflow_id)
    handler_function = getattr(app.tasks, handler)
    # This algorithm will always try and run at least one task
    longest_task_ms = 0

    for i in range(next_task, tasks + 1):
        time.sleep(delay_ms / 1000.0)

        def handler_begin_task():
            return begin_task(uid, workflow_id, tasks, i)

        def handler_end_task():
            return end_task(uid, workflow_id, tasks, i)

        now = time.time()
        handler_function(next_task, tasks, handler_begin_task, handler_end_task)
        elapsed_ms = (time.time() - now) * 1000
        if elapsed_ms > longest_task_ms:
            longest_task_ms = elapsed_ms
        remaining_ms = context.get_remaining_time_in_millis()
        needed_ms = (longest_task_ms * safety_multiple) + safety_delay_ms + delay_ms
        if remaining_ms < needed_ms:
            raise Error(
                f"Out of time to run the next task. Need {needed_ms} ms but only have {remaining_ms}"
            )

    end_workflow(uid, workflow_id)
    # This becomes the output of the state machine
    event["success"] = True
    return event
