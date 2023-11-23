import datetime
import importlib
import os
import tasks.driver
import time
import uuid


def run(workflow_id):
    # Here the event is whatever you pass as the JSON when executing the stepfunctions state machine
    uid = str(uuid.uuid4())
    delay_ms = int((os.environ.get("DELAY_MS", "0")))

    print(workflow_id, uid, delay_ms)

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

    print(next_task, state)
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

    print("Longest task (ms):", longest_task_ms)
    tasks.driver.end_workflow(uid, workflow_id)
    return True


if __name__ == "__main__":
    import sys

    run(sys.argv[1])
