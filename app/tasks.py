import time


def wait():
    time.sleep(3)


def count(next_task, state, patch_state):
    print(next_task, state)
    if next_task == 1:
        print("Patching state")
        patch_state({"banana": "fruit"})
    wait()
