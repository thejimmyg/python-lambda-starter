import datetime
import json
import os

import boto3

stepfunctions = boto3.client(
    service_name="stepfunctions", region_name=os.environ["AWS_REGION"]
)
store = "tasks"

import kvstore.driver


def begin_workflow(uid, tasks, handler):
    begin = datetime.datetime.now()
    begin_isoformat = begin.isoformat()
    pk = f"{begin_isoformat}/{uid}"
    kvstore.driver.put(
        store,
        pk,
        {
            "tasks": int(tasks),
            "handler": str(handler),
            "begin": begin_isoformat,
            "begin_uid": str(uid),
        },
    )
    return pk


def get_next_task(workflow_id):
    r = list(kvstore.driver.iterate(store, workflow_id, limit=2, consistent=True))
    if len(r) == 0:
        raise Exception(f'No such workflow "workflow/{workflow_id}"')
    elif len(r) == 1:
        # No tasks yet
        next_task = 1
    else:
        sk, data = r[1]
        assert sk.startswith("/task/"), sk
        end = data.get("end")
        if end:
            next_task = int(sk.split("/")[-1]) + 1
        else:
            next_task = int(sk.split("/")[-1])
    get_workflow_response = r[0][1]
    tasks: float = get_workflow_response["tasks"]
    handler: str = get_workflow_response["handler"]
    return int(next_task), int(tasks), handler


def progress(workflow_id):
    r = list(kvstore.driver.iterate(store, workflow_id))
    header = dict(
        workflow_id=workflow_id,
        tasks=int(r[0][1]["tasks"]),
        begin=r[0][1]["begin"],
        end=r[0][1].get("end"),
    )
    tasks = []
    for sk, data in r[1:]:
        assert sk.startswith("/task/"), sk
        _, _, remaining, task = sk.split("/")
        tasks.append(
            dict(
                task=int(task),
                remaining=int(remaining),
                begin=data["begin"],
                end=data.get("end"),
            )
        )
    return header, tasks


def begin_task(uid, workflow_id, tasks, i):
    now = datetime.datetime.now()
    sk = f"/task/{tasks-i}/{i}"
    put_task_response = kvstore.driver.put(
        store,
        workflow_id,
        sk=sk,
        data={
            "begin": now.isoformat(),
            "begin_uid": uid,
        },
    )


def end_task(uid, workflow_id, tasks, i):
    now = datetime.datetime.now()
    sk = f"/task/{tasks-i}/{i}"
    end_task_response = kvstore.driver.update(
        store,
        workflow_id,
        sk=sk,
        data={
            "end": now.isoformat(),
            "end_uid": uid,
        },
    )
    # print(end_task_response)


def end_workflow(uid, workflow_id):
    now = datetime.datetime.now()
    end_workflow_response = kvstore.driver.update(
        store,
        workflow_id,
        sk="/",
        data={
            "end": now.isoformat(),
            "end_uid": uid,
        },
    )
    # print(end_workflow_response)


def begin_state_machine(workflow_id):
    response = stepfunctions.start_execution(
        stateMachineArn=os.environ["TASKS_STATE_MACHINE_ARN"],
        input=json.dumps({"workflow_id": workflow_id}),
    )
    # print(response)
    return dict(success=True)