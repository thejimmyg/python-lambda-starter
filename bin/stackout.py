import json
import sys


def filter_first_stack_outputs(stacks):
    return {
        o["OutputKey"]: o.get("OutputValue")
        for o in stacks["Stacks"][0].get("Outputs", [])
    }


print(json.dumps(filter_first_stack_outputs(json.loads(sys.stdin.read())), indent=2))
