import os

if os.environ.get("TASKS_STATE_MACHINE_ARN"):
    from .kvstore_aws_step_functions import (
        begin_state_machine,
        begin_task,
        begin_workflow,
        end_task,
        end_workflow,
        get_next_task,
        progress,
        patch_state,
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
        patch_state,
    )


__all__ = (
    "begin_workflow",
    "get_next_task",
    "progress",
    "begin_task",
    "end_task",
    "end_workflow",
    "begin_state_machine",
    "patch_state",
)
