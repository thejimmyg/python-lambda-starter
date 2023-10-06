import json
import shlex
import sys


def camel_to_snake(s):
    return "".join(["_" + c.lower() if c.isupper() else c for c in s]).lstrip("_")


def dict_to_shell(vars):
    output = ""
    for k, v in vars.items():
        if type(v) in [dict, list]:
            v = json.dumps(v)
        output += f"{camel_to_snake(k).upper()}={shlex.quote(str(v))}\n"
    return output


print(dict_to_shell(json.loads(sys.stdin.read() or "{}")), end="")
