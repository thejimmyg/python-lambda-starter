import json
import os

import boto3

from .kvstore_local import (
    begin_task,
    begin_workflow,
    end_task,
    end_workflow,
    get_next_task,
    progress,
)

__all__ = [
    "begin_workflow",
    "get_next_task",
    "progress",
    "begin_task",
    "end_task",
    "end_workflow",
    "begin_state_machine",
]
stepfunctions = boto3.client(
    service_name="stepfunctions", region_name=os.environ["AWS_REGION"]
)
store = "tasks"


def begin_state_machine(workflow_id):
    response = stepfunctions.start_execution(
        stateMachineArn=os.environ["TASKS_STATE_MACHINE_ARN"],
        input=json.dumps({"store": store, "workflow_id": workflow_id}),
    )
    # print(response)
    return dict(success=True)
