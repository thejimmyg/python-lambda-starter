from dataclasses import dataclass
import datetime
from typing import Any


class Abort(Exception):
    pass


class OutOfTime(Exception):
    pass


class RenderableTaskAbort(Abort):
    def render(self):
        # Return a correctly escaped HTML string to use instead of the current task.correctly_escaped_html_status_message
        return "Abort"


@dataclass
class Task:
    number: int
    correctly_escaped_html_status_message: str
    workflow_state: dict[str, int | float | str]
    patch_workflow_state: Any
    end_state_patches: dict[str, int | float | str]
    get_task_state: Any
    _begun: list[bool]
    begin: Any
    Abort: type[Abort]
    OutOfTime: type[OutOfTime]


import tasks.driver


def make_task(uid, workflow_id, workflow_state, patch_workflow_state, number):
    begun = [False]
    begun_at = datetime.datetime.now()

    def get_task_state(number):
        data, ttl = tasks.driver.get_task(
            workflow_id, int(workflow_state["num_tasks"]), number
        )
        return data

    def begin(correctly_escaped_html_status_message, task_state=None):
        begun[0] = True
        tasks.driver.begin_task(
            uid,
            workflow_id,
            workflow_state["num_tasks"],
            number,
            correctly_escaped_html_status_message,
            task_state,
            begun_at,
        )

    return Task(
        number=number,
        correctly_escaped_html_status_message="",
        workflow_state=workflow_state,
        patch_workflow_state=patch_workflow_state,
        end_state_patches={},
        get_task_state=get_task_state,
        _begun=begun,
        begin=begin,
        Abort=Abort,
        OutOfTime=OutOfTime,
    )
