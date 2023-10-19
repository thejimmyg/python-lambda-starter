import datetime
import json
import os

import boto3

TABLE_NAME = os.environ["TASKS_DYNAMODB_TABLE_NAME"]
STATE_MACHINE_ARN = os.environ["TASKS_STATE_MACHINE_ARN"]

stepfunctions = boto3.client(
    service_name="stepfunctions", region_name=os.environ["AWS_REGION"]
)
dynamodb = boto3.client(service_name="dynamodb", region_name=os.environ["AWS_REGION"])


def begin_workflow(tasks):
    begin = datetime.datetime.now()
    begin_isoformat = begin.isoformat()
    pk = f"workflow/{begin_isoformat}"
    dynamodb.put_item(
        TableName=TABLE_NAME,
        Item={
            "pk": {"S": pk},
            "sk": {"S": "/"},
            "tasks": {"N": str(tasks)},
            "begin": {"S": begin_isoformat},
        },
    )
    return begin.isoformat()


def get_next_task(workflow_id):
    r = dynamodb.query(
        TableName=TABLE_NAME,
        KeyConditions={
            "pk": {
                "ComparisonOperator": "EQ",
                "AttributeValueList": [{"S": f"workflow/{workflow_id}"}],
            }
        },
        ConsistentRead=True,
        Limit=2,
    )
    if len(r["Items"]) == 1:
        # No tasks yet
        next_task = 1
    else:
        sk = r["Items"][1]["sk"]["S"]
        assert sk.startswith("/task/"), sk
        next_task = int(sk.split("/")[-1]) + 1
    get_workflow_response = r["Items"][0]
    tasks = int(get_workflow_response["tasks"]["N"])
    return next_task, tasks


def progress(workflow_id):
    r = dynamodb.query(
        TableName=TABLE_NAME,
        KeyConditions={
            "pk": {
                "ComparisonOperator": "EQ",
                "AttributeValueList": [{"S": f"workflow/{workflow_id}"}],
            }
        },
    )
    header = dict(
        workflow_id=workflow_id,
        tasks=int(r["Items"][0]["tasks"]["N"]),
        begin=r["Items"][0]["begin"]["S"],
        end=r["Items"][0].get("end", {"S": None})["S"],
    )
    tasks = []
    for item in r["Items"][1:]:
        sk = item["sk"]["S"]
        assert sk.startswith("/task/"), sk
        _, _, remaining, task = sk.split("/")
        tasks.append(
            dict(
                task=int(task),
                remaining=int(remaining),
                begin=item["begin"]["S"],
                end=item.get("end", {"S": None})["S"],
            )
        )
    return header, tasks


def begin_task(workflow_id, tasks, i):
    now = datetime.datetime.now()
    print(f"workflow/{workflow_id} {i}/{tasks}")
    pk = {"S": f"workflow/{workflow_id}"}
    sk = {"S": f"/task/{tasks-i}/{i}"}
    put_task_response = dynamodb.put_item(
        TableName=TABLE_NAME,
        Item={
            "pk": pk,
            "sk": sk,
            "begin": {"S": now.isoformat()},
        },
    )


def end_task(workflow_id, tasks, i):
    now = datetime.datetime.now()
    pk = {"S": f"workflow/{workflow_id}"}
    sk = {"S": f"/task/{tasks-i}/{i}"}
    dynamodb.update_item(
        TableName=TABLE_NAME,
        Key={
            "pk": pk,
            "sk": sk,
        },
        AttributeUpdates={
            "end": {
                "Value": {"S": now.isoformat()},
                "Action": "PUT",
            },
        },
    )


def end_workflow(workflow_id):
    end_workflow_response = dynamodb.update_item(
        TableName=TABLE_NAME,
        Key={
            "pk": {"S": f"workflow/{workflow_id}"},
            "sk": {"S": "/"},
        },
        AttributeUpdates={
            "end": {
                "Value": {"S": datetime.datetime.now().isoformat()},
                "Action": "PUT",
            }
        },
    )
    print(end_workflow_response)


def begin_state_machine(workflow_id):
    response = stepfunctions.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        input=json.dumps({"workflow": workflow_id}),
    )
    print(response)
    return dict(success=True)
