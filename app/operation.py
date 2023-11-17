import os
import uuid

import tasks.driver

from .typeddicts import (
    SubmitInput,
    SubmitInputResponse,
    ProgressResponse,
    is_ProgressResponse,
    is_SubmitInputResponse,
)


def submit_input(input: SubmitInput) -> SubmitInputResponse:
    uid = str(uuid.uuid4())
    if input["password"] != os.environ["PASSWORD"]:
        raise ValueError("Invalid password")
    else:
        workflow_id = tasks.driver.begin_workflow(uid=uid, num_tasks=2, handler="count")
        tasks.driver.begin_state_machine(workflow_id)
        submit_input_response = dict(workflow_id=workflow_id)
        assert is_SubmitInputResponse(submit_input_response)
        return submit_input_response


def progress(workflow_id: str) -> ProgressResponse:
    progress, task_list = tasks.driver.progress(workflow_id=workflow_id)
    progress_response = progress.copy()
    if task_list:
        progress_response["tasks"] = task_list
    assert is_ProgressResponse(progress_response)
    return progress_response
