import os

if os.environ.get("TASKS_STATE_MACHINE_ARN") and os.environ.get("AWS_REGION"):
    from .kvstore_aws_step_functions import (
        begin_state_machine,
        begin_task,
        begin_workflow,
        end_task,
        end_workflow,
        get_next_task,
        progress,
    )
else:
    from .kvstore_local import (
        begin_state_machine,
        begin_task,
        begin_workflow,
        end_task,
        end_workflow,
        get_next_task,
        progress,
    )


__all__ = (
    "begin_workflow",
    "get_next_task",
    "progress",
    "begin_task",
    "end_task",
    "end_workflow",
    "begin_state_machine",
)
