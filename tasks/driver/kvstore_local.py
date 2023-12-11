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
    assert "status" not in state
    assert "execution" not in state
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
        task_state = None
    else:
        sk, task_state, ttl = results[1]
        assert sk.startswith("/task/"), sk
        end = task_state.get("end")
        if end:
            next_task = int(sk.split("/")[-1]) + 1
        else:
            next_task = int(sk.split("/")[-1])
    state = results[0][1].copy()
    state["num_tasks"] = int(state["num_tasks"])
    return int(next_task), state, task_state


def progress(workflow_id, limit=40):
    results, maybe_more_sk = list(
        kvstore.driver.iterate(store, workflow_id, limit=limit)
    )
    header = results[0][1]
    header["num_tasks"] = int(header["num_tasks"])
    del header["handler"]
    task_list = []
    task_number = 0
    remaining = header["num_tasks"]
    if len(results) > 1:
        sk, data, ttl = results[1]
        assert sk.startswith("/task/"), sk
        _, _, remaining, task_number = sk.split("/")
        task_number = int(task_number)
    for sk, data, ttl in results[1:]:
        assert sk.startswith("/task/"), sk
        _, _, remaining, task_number_ = sk.split("/")
        t = dict(
            task=int(task_number_),
            remaining=int(remaining),
        )
        t.update(data)
        task_list.append(t)
    return header, task_list, int(task_number)


def begin_task(
    uid,
    workflow_id,
    num_tasks,
    i,
    correctly_escaped_html_status_message: str,
    task_state: dict[str, int | float | str] | None = None,
    begun_at: datetime.datetime | None = None,
):
    if begun_at is None:
        datetime.datetime.now()
    # Help the type checker
    assert begun_at
    pad_length = len(str(num_tasks))
    sk = f"/task/{str(num_tasks-i).zfill(pad_length)}/{str(i).zfill(pad_length)}"
    data = {
        "begin": begun_at.isoformat(),
        "begin_uid": uid,
        "correctly_escaped_html_status_message": correctly_escaped_html_status_message,
    }
    if task_state is not None:
        assert "correctly_escaped_html_status_message" not in task_state
        assert "task" not in task_state
        assert "remaining" not in task_state
        assert "begin" not in task_state
        assert "begin_uid" not in task_state
        assert "end" not in task_state
        assert "end_uid" not in task_state
        data.update(task_state)
    put_task_response = kvstore.driver.put(
        store,
        workflow_id,
        sk=sk,
        data=data,
    )


def get_task(workflow_id, num_tasks, i):
    sk = f"/task/{str(num_tasks-i).zfill(len(str(num_tasks)))}/{str(i).zfill(len(str(num_tasks)))}"
    return kvstore.driver.get(store, pk=workflow_id, sk=sk)


def end_task(
    uid,
    workflow_id,
    num_tasks,
    i,
    correctly_escaped_html_status_message=None,
    patch_task_state: dict[str, int | float | str | kvstore.driver.Remove]
    | None = None,
    ended_at: datetime.datetime | None = None,
):
    if ended_at is None:
        ended_at = datetime.datetime.now()
    # Help the type checker
    assert ended_at
    data = {
        "end": ended_at.isoformat(),
        "end_uid": uid,
    }
    if patch_task_state is not None:
        assert "task" not in patch_task_state
        assert "correctly_escaped_html_status_message" not in patch_task_state
        assert "remaining" not in patch_task_state
        assert "begin" not in patch_task_state
        assert "begin_uid" not in patch_task_state
        assert "end" not in patch_task_state
        assert "end_uid" not in patch_task_state
        data.update(patch_task_state)
    pad_length = len(str(num_tasks))
    sk = f"/task/{str(num_tasks-i).zfill(pad_length)}/{str(i).zfill(pad_length)}"
    kvstore.driver.patch(store, workflow_id, sk=sk, data=data)


def end_workflow(uid, workflow_id, status="SUCCEEDED"):
    assert status in ["SUCCEEDED", "FAILED"]
    now = datetime.datetime.now()
    kvstore.driver.patch(
        store,
        workflow_id,
        sk="/",
        data={"end": now.isoformat(), "end_uid": uid, "status": status},
    )


def _patch_state(
    workflow_id, data: dict[str, str | int | float | kvstore.driver.Remove]
):
    assert "workflow_id" not in data
    assert "num_tasks" not in data
    assert "begin" not in data
    assert "begin_uid" not in data
    assert "end" not in data
    assert "end_uid" not in data
    assert "handler" not in data
    assert "status" not in data
    kvstore.driver.patch(
        store,
        workflow_id,
        sk="/",
        data=data,
    )


def patch_state(
    workflow_id, data: dict[str, str | int | float | kvstore.driver.Remove]
):
    assert "execution" not in data
    return _patch_state(workflow_id=workflow_id, data=data)


import subprocess
import sys


def begin_state_machine(workflow_id):
    process = subprocess.Popen(
        [sys.executable, "tasks/adapter/process.py", workflow_id]
    )
    _patch_state(workflow_id, {"execution": str(process.pid)})
    return str(process.pid)


def get_execution_status(pid):
    return "UNKNOWN"
