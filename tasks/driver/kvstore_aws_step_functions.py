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
    patch_state,
    _patch_state,
    get_task,
)

__all__ = [
    "begin_workflow",
    "get_next_task",
    "progress",
    "begin_task",
    "end_task",
    "end_workflow",
    "patch_state",
    "begin_state_machine",
    "get_execution_status",
    "get_task",
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
    _patch_state(workflow_id, {"execution": response["executionArn"]})
    return response["executionArn"]


def get_execution_status(executionArn):
    return stepfunctions.describe_execution(executionArn=executionArn)["status"]
