import datetime

store = "tasks"

import kvstore.driver


def begin_workflow(uid, num_tasks, handler, state=None):
    begin = datetime.datetime.now()
    begin_isoformat = begin.isoformat()
    pk = f"{begin_isoformat}/{uid}"
    if state is None:
        state = {}
    assert "num_tasks" not in state
    assert "handler" not in state
    assert "begin" not in state
    assert "begin_uid" not in state
    assert "end" not in state
    assert "end_uid" not in state
    data = {
        "num_tasks": int(num_tasks),
        "handler": str(handler),
        "begin": begin_isoformat,
        "begin_uid": str(uid),
    }
    data.update(state)
    kvstore.driver.put(
        store,
        pk,
        data,
    )
    return pk


def get_next_task(workflow_id):
    results, maybe_more_sk = list(
        kvstore.driver.iterate(store, workflow_id, limit=2, consistent=True)
    )
    if len(results) == 0:
        raise Exception(f'No such workflow "{workflow_id}"')
    elif len(results) == 1:
        # No tasks yet
        next_task = 1
    else:
        sk, data, ttl = results[1]
        assert sk.startswith("/task/"), sk
        end = data.get("end")
        if end:
            next_task = int(sk.split("/")[-1]) + 1
        else:
            next_task = int(sk.split("/")[-1])
    state = results[0][1].copy()
    state["num_tasks"] = int(state["num_tasks"])
    return int(next_task), state


def progress(workflow_id):
    results, maybe_more_sk = list(kvstore.driver.iterate(store, workflow_id))
    workflow = results[0]
    header = dict(
        workflow_id=workflow_id,
        num_tasks=int(workflow[1]["num_tasks"]),
        begin=workflow[1]["begin"],
    )
    if "end" in workflow[1]:
        header["end"] = workflow[1].get("end")
    task_list = []
    for sk, data, ttl in results[1:]:
        assert sk.startswith("/task/"), sk
        _, _, remaining, task = sk.split("/")
        t = dict(
            task=int(task),
            remaining=int(remaining),
            begin=data["begin"],
        )
        if data.get("end"):
            t["end"] = data["end"]
        task_list.append(t)
    return header, task_list


def begin_task(uid, workflow_id, num_tasks, i):
    now = datetime.datetime.now()
    sk = f"/task/{num_tasks-i}/{i}"
    put_task_response = kvstore.driver.put(
        store,
        workflow_id,
        sk=sk,
        data={
            "begin": now.isoformat(),
            "begin_uid": uid,
        },
    )


def end_task(uid, workflow_id, num_tasks, i):
    now = datetime.datetime.now()
    sk = f"/task/{num_tasks-i}/{i}"
    kvstore.driver.patch(
        store,
        workflow_id,
        sk=sk,
        data={
            "end": now.isoformat(),
            "end_uid": uid,
        },
    )


def end_workflow(uid, workflow_id):
    now = datetime.datetime.now()
    kvstore.driver.patch(
        store,
        workflow_id,
        sk="/",
        data={
            "end": now.isoformat(),
            "end_uid": uid,
        },
    )


def patch_state(workflow_id, data: dict[str, str | int | float]):
    kvstore.driver.patch(
        store,
        workflow_id,
        sk="/",
        data=data,
    )


import subprocess
import sys


def begin_state_machine(workflow_id):
    process = subprocess.Popen(
        [sys.executable, "tasks/adapter/process.py", workflow_id]
    )
    return dict(success=True, pid=process.pid)
