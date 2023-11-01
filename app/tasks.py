import time


def wait():
    time.sleep(3)


def count(next_task, num_tasks, begin_task, end_task):
    # This only makes sense if there is a payload
    begin_task()
    wait()
    end_task()
