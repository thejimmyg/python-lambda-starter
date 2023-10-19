import datetime
import json
import os

import boto3

stepfunctions = boto3.client(
    service_name="stepfunctions", region_name=os.environ["AWS_REGION"]
)
dynamodb = boto3.client(service_name="dynamodb", region_name=os.environ["AWS_REGION"])


def begin_workflow(uid, tasks, handler):
    begin = datetime.datetime.now()
    begin_isoformat = begin.isoformat()
    pk = f"workflow/{begin_isoformat}/{uid}"
    dynamodb.put_item(
        TableName=os.environ["TASKS_DYNAMODB_TABLE_NAME"],
        Item={
            "pk": {"S": pk},
            "sk": {"S": "/"},
            "tasks": {"N": str(tasks)},
            "handler": {"S": str(handler)},
            "begin": {"S": begin_isoformat},
            "begin_uid": {"S": uid},
        },
    )
    return f"{begin_isoformat}/{uid}"


def get_next_task(workflow_id):
    r = dynamodb.query(
        TableName=os.environ["TASKS_DYNAMODB_TABLE_NAME"],
        KeyConditions={
            "pk": {
                "ComparisonOperator": "EQ",
                "AttributeValueList": [{"S": f"workflow/{workflow_id}"}],
            }
        },
        ConsistentRead=True,
        Limit=2,
    )
    if len(r["Items"]) == 0:
        raise Exception(f'No such workflow "workflow/{workflow_id}"')
    elif len(r["Items"]) == 1:
        # No tasks yet
        next_task = 1
    else:
        sk = r["Items"][1]["sk"]["S"]
        assert sk.startswith("/task/"), sk
        end = r["Items"][1].get("end", {"S": None})["S"]
        if end:
            next_task = int(sk.split("/")[-1]) + 1
        else:
            next_task = int(sk.split("/")[-1])
    get_workflow_response = r["Items"][0]
    tasks = int(get_workflow_response["tasks"]["N"])
    handler = get_workflow_response["handler"]["S"]
    return next_task, tasks, handler


def progress(workflow_id):
    r = dynamodb.query(
        TableName=os.environ["TASKS_DYNAMODB_TABLE_NAME"],
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


def begin_task(uid, workflow_id, tasks, i):
    now = datetime.datetime.now()
    print(f"workflow/{workflow_id} {i}/{tasks}")
    pk = {"S": f"workflow/{workflow_id}"}
    sk = {"S": f"/task/{tasks-i}/{i}"}
    put_task_response = dynamodb.put_item(
        TableName=os.environ["TASKS_DYNAMODB_TABLE_NAME"],
        Item={
            "pk": pk,
            "sk": sk,
            "begin": {"S": now.isoformat()},
            "begin_uid": {"S": uid},
        },
    )


def end_task(uid, workflow_id, tasks, i):
    now = datetime.datetime.now()
    pk = {"S": f"workflow/{workflow_id}"}
    sk = {"S": f"/task/{tasks-i}/{i}"}
    dynamodb.update_item(
        TableName=os.environ["TASKS_DYNAMODB_TABLE_NAME"],
        Key={
            "pk": pk,
            "sk": sk,
        },
        AttributeUpdates={
            "end": {
                "Value": {"S": now.isoformat()},
                "Action": "PUT",
            },
            "end_uid": {
                "Value": {"S": uid},
                "Action": "PUT",
            },
        },
    )


def end_workflow(uid, workflow_id):
    end_workflow_response = dynamodb.update_item(
        TableName=os.environ["TASKS_DYNAMODB_TABLE_NAME"],
        Key={
            "pk": {"S": f"workflow/{workflow_id}"},
            "sk": {"S": "/"},
        },
        AttributeUpdates={
            "end": {
                "Value": {"S": datetime.datetime.now().isoformat()},
                "Action": "PUT",
            },
            "end_uid": {
                "Value": {"S": uid},
                "Action": "PUT",
            },
        },
    )
    print(end_workflow_response)


def begin_state_machine(workflow_id):
    response = stepfunctions.start_execution(
        stateMachineArn=os.environ["TASKS_STATE_MACHINE_ARN"],
        input=json.dumps({"workflow_id": workflow_id}),
    )
    print(response)
    return dict(success=True)
