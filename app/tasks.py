import time


def count(next_task, tasks, begin_task, end_task):
    # This only makes sense if there is a payload
    begin_task()
    time.sleep(0.5)
    end_task()


from driver.tasks.auto import begin_task, end_task, end_workflow, get_next_task


def process(workflow_id, handler):
    next_task, tasks = get_next_task(workflow_id)
    for i in range(next_task, tasks + 1):
        try:

            def handler_begin_task():
                return begin_task(workflow_id, tasks, i)

            def handler_end_task():
                return end_task(workflow_id, tasks, i)

            handler(next_task, tasks, handler_begin_task, handler_end_task)
        except:
            # If begin_task has been called, need to update it with an error, and then do we retry it from there and error if there are 10 failures?
            raise
    end_workflow(workflow_id)
    # begin_state_machine(workflow_id)
    return dict(success=True)
