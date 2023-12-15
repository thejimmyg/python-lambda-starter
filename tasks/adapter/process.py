import datetime
import importlib
import os
import tasks.driver
import time
import uuid


from tasks.adapter.shared import make_task, Abort, RenderableTaskAbort


def run(workflow_id):
    # Here the event is whatever you pass as the JSON when executing the stepfunctions state machine
    uid = str(uuid.uuid4())
    delay_ms = int((os.environ.get("DELAY_MS", "0")))

    print(workflow_id, uid, delay_ms)

    next_task, workflow_state, data = tasks.driver.get_next_task(workflow_id)
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
        now = time.time()
        task = make_task(
            uid,
            workflow_id=workflow_id,
            workflow_state=workflow_state,
            patch_workflow_state=patch_workflow_state,
            number=number,
        )

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
                task.correctly_escaped_html_status_message,
                task.end_state_patches,
                datetime.datetime.now(),
            )
            raise
        else:
            tasks.driver.end_task(
                uid,
                workflow_id,
                workflow_state["num_tasks"],
                number,
                task.correctly_escaped_html_status_message,
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

    print("Longest task (ms):", longest_task_ms)
    tasks.driver.end_workflow(uid, workflow_id)
    return True


if __name__ == "__main__":
    import sys

    run(sys.argv[1])
