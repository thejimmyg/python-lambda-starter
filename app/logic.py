import os

import tasks.driver

from .typeddicts import ApiResponse, SubmitInput


def submit(context: dict, input: SubmitInput) -> ApiResponse:
    if input["password"] != os.environ["PASSWORD"]:
        raise ValueError("Invalid password")
    else:
        workflow_id = tasks.driver.begin_workflow(
            uid=context["uid"], num_tasks=2, handler="count"
        )
        tasks.driver.begin_state_machine(workflow_id)
        return dict(success=True)
