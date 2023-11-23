import time


def wait():
    time.sleep(3)


def count(task_number, state, patch_state, register_begin, register_end):
    print(task_number, state)
    register_begin(task_state={"starting": task_number})
    if task_number == 1:
        print("Patching state")
        patch_state({"banana": "fruit"})
    wait()
    register_end(patch_task_state={"ending": task_number})
