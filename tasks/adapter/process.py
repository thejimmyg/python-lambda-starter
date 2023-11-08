import os
import time
import uuid

# XXX I'm not happy with this part of the design.
import app.tasks
import tasks.driver


def run(workflow_id):
    # Here the event is whatever you pass as the JSON when executing the stepfunctions state machine
    uid = str(uuid.uuid4())
    delay_ms = int((os.environ.get("DELAY_MS", "0")))

    print(workflow_id, uid, delay_ms)

    next_task, num_tasks, handler = tasks.driver.get_next_task(workflow_id)
    handler_function = getattr(app.tasks, handler)
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
        elapsed_ms: float = (time.time() - now) * 1000
        if elapsed_ms > longest_task_ms:
            longest_task_ms = elapsed_ms

    print("Longest task:", longest_task_ms)
    tasks.driver.end_workflow(uid, workflow_id)
    return True


if __name__ == "__main__":
    import sys

    run(sys.argv[1])
