import os

if os.environ.get("AWS_REGION") is not None:
    # Assume we are in a lambda environment
    from .dynamodb import (
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
else:
    raise Exception(
        "Only a DynamoDB adapter for a lambda environment is currently implemented"
    )
