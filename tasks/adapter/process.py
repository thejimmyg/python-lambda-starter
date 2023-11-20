import os
import time
import uuid
import tasks.driver
import importlib


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
        # End new
        now = time.time()
        tasks.driver.begin_task(uid, workflow_id, state["num_tasks"], i)
        handler_function(i, state, patch_state)
        tasks.driver.end_task(uid, workflow_id, state["num_tasks"], i)

        elapsed_ms: float = (time.time() - now) * 1000
        if elapsed_ms > longest_task_ms:
            longest_task_ms = elapsed_ms

    print("Longest task (ms):", longest_task_ms)
    tasks.driver.end_workflow(uid, workflow_id)
    return True


if __name__ == "__main__":
    import sys

    run(sys.argv[1])
