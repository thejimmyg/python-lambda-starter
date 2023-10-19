import os
import time

from driver.tasks.auto import (
    begin_state_machine,
    begin_task,
    begin_workflow,
    end_task,
    end_workflow,
    get_next_task,
)

from .typeddicts import ApiResponse, SubmitInput


def submit(input: SubmitInput) -> ApiResponse:
    if input["password"] != os.environ["PASSWORD"]:
        raise ValueError("Invalid password")
    else:
        workflow_id = begin_workflow(tasks=2)
        next_task, tasks = get_next_task(workflow_id)
        for i in range(next_task, tasks + 1):
            begin_task(workflow_id, tasks, i)
            time.sleep(0.5)
            end_task(workflow_id, tasks, i)
        end_workflow(workflow_id)
        begin_state_machine(workflow_id)
        return dict(success=True)
