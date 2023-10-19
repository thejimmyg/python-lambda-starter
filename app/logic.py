import os

from driver.tasks.auto import begin_state_machine, begin_workflow

from .typeddicts import ApiResponse, SubmitInput


def submit(context: dict, input: SubmitInput) -> ApiResponse:
    if input["password"] != os.environ["PASSWORD"]:
        raise ValueError("Invalid password")
    else:
        workflow_id = begin_workflow(uid=context["uid"], tasks=2, handler='count')
        begin_state_machine(workflow_id)
        return dict(success=True)
