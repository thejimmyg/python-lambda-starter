import time
from template import Html
from tasks.adapter.shared import RenderableTaskAbort


def wait():
    time.sleep(3)


class InvalidCount(RenderableTaskAbort):
    def __init__(self, count):
        self.count = count
        super().__init__(self, "Unexpected count")

    def render(self):
        return Html("<strong>Abort:</strong> Got an invalid count: ") + str(self.count)


def count(task):
    print(task.number, task.workflow_state)
    task.begin("Starting ...", {"starting": task.number})
    if task.number == 1:
        print("Patching workflow state")
        task.patch_workflow_state({"banana": "fruit"})
    if task.number == 100:
        raise InvalidCount(task.number)
    wait()
    # This will be saved at the end of the task
    task.end_state_patches["ending"] = task.number
