from typing import Literal, NotRequired, TypedDict

JsonschemaObject = TypedDict(
    "JsonschemaObject",
    {
        "$id": str,
        "$schema": Literal["https://json-schema.org/draft/2020-12/schema"],
        "title": str,
        "type": "object",
        "properties": dict[str, dict[str, str]],
        "required": NotRequired[list[str]],
    },
)

submit_input_jsonschema: JsonschemaObject = {
    "$id": "https://example.com/person.schema.json",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "SubmitInput",
    "type": "object",
    "properties": {
        "password": {
            "type": "string",
            "description": "The password to authorize this request.",
        },
        "id": {"type": "integer", "description": "The ID of the object to submit"},
    },
}


response_jsonschema: JsonschemaObject = {
    "$id": "https://example.com/person.schema.json",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ApiResponse",
    "type": "object",
    "required": ["success"],
    "properties": {
        "success": {
            "type": "boolean",
            "description": "Whether the request succeded or not.",
        }
    },
}


jsonschema_types_to_python_types: dict[str, str] = {
    "string": "str",
    "integer": "int",
    "boolean": "bool",
}

forward_references = []


def encode_type(t):
    if t in forward_references:
        return '"' + t + '"'
    return t


print("from typing import TypedDict, TypeGuard, NotRequired")
for jsonschema in [
    submit_input_jsonschema,
    response_jsonschema,
]:
    print()
    print()
    print(f"{jsonschema['title']} = TypedDict('{jsonschema['title']}', " + "{")
    for key, value in jsonschema["properties"].items():
        if key in jsonschema.get("required", []):
            print(
                f"    '{key}': {encode_type(jsonschema_types_to_python_types[value['type']])},"
            )
        else:
            print(
                f"    '{key}': NotRequired[{encode_type(jsonschema_types_to_python_types[value['type']])}],"
            )
    print("})")
    print()
    print()
    print(
        f"def is_{jsonschema['title'].lower()}(value: dict) -> TypeGuard[{jsonschema['title']}]:"
    )
    print("    try:")
    for key, value in jsonschema["properties"].items():
        if key in jsonschema.get("required", []):
            print(
                f"        assert isinstance(value['{key}'], {jsonschema_types_to_python_types[value['type']]})"
            )
        else:
            print(f"        if '{key}' in value:")
            print(
                f"            assert isinstance(value['{key}'], {jsonschema_types_to_python_types[value['type']]})"
            )
    print("        return True")
    print("    except (KeyError, AssertionError):")
    print("        return False")
