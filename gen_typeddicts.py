import json
import warnings
from typing import Any, Literal, NotRequired, Optional, TypedDict

SecurityScheme = TypedDict(
    "SecurityScheme",
    {
        "type": Literal["apiKey"],
        "in": Literal["header"],
        "name": str,
    },
)

JsonschemaObject = TypedDict(
    "JsonschemaObject",
    {
        "title": str,
        "type": "object",
        "properties": dict[str, dict[str, str]],
        "required": NotRequired[list[str]],
        "securitySchemes": list[SecurityScheme],
    },
)

Schema = TypedDict(
    "Schema",
    {
        "type": Literal["string"],
        "format": Optional[Literal["mask"]],
    },
)

Parameter = TypedDict(
    "Parameter",
    {
        "name": str,
        "in": Literal["path"] | Literal["query"],
        "required": bool,
        "schema": Schema,
    },
)

RequestBody = TypedDict(
    "RequestBody",
    {
        "content": dict[str, Any],
        "required": bool,
    },
)


Operation = TypedDict(
    "Operation",
    {
        "path": str,
        "method": str,
        "operationId": str,
        "parameters": list[Parameter],
        "requestBody": RequestBody,
        "responses": Any,
    },
)


def generate_warnings(filename: str, openapi: dict[str, Any]):
    assert openapi["openapi"] == "3.0.1", openapi["openapi"]
    for key in openapi:
        if key not in ["openapi", "components", "paths"]:
            warnings.warn(f"{repr(filename)} OpenAPI key {repr(key)} is ignored.")
    for title in openapi["components"]["schemas"].keys():
        jsonschema = openapi["components"]["schemas"][title]
        for key in jsonschema:
            if key not in ["type", "properties", "required"]:
                warnings.warn(
                    f"{repr(filename)} OpenAPI components/schemas {repr(title)} {repr(key)} is ignored."
                )
        for property in jsonschema["properties"]:
            for property_key in jsonschema["properties"][property]:
                if property_key not in ["type", "items", "properties", "$ref"] + [
                    "description",
                    "title",
                ]:
                    warnings.warn(
                        f"{repr(filename)} OpenAPI components/schemas {repr(title)} properties {repr(property)} {repr(property_key)} is ignored."
                    )
    for security_scheme in openapi["components"].get("securitySchemes", {}).values():
        for security_scheme_key in security_scheme.keys():
            if security_scheme_key not in ["type", "in", "name"]:
                warnings.warn(
                    f"{repr(filename)} OpenAPI 'securitySchemes' item {repr(security_scheme)} has a key {repr(security_scheme_key)} which is ignored."
                )
            assert security_scheme["type"] == "apiKey", security_scheme["type"]
            assert security_scheme["in"] == "header", security_scheme["in"]
            assert type(security_scheme["name"]) is str, security_scheme
    for key in openapi["components"]:
        if key not in ["schemas", "securitySchemes"]:
            warnings.warn(
                f"{repr(filename)} OpenAPI 'components' key {repr(key)} is ignored."
            )
    for path in openapi["paths"]:
        for method in openapi["paths"][path]:
            assert method in ["get", "post"], method
            for key in openapi["paths"][path][method]:
                if key not in [
                    "operationId",
                    "parameters",
                    "responses",
                    "requestBody",
                ] + [
                    "description",
                    "tags",
                    "summary",
                ]:
                    warnings.warn(
                        f"{repr(filename)} OpenAPI paths {repr(path)} {repr(method)} {repr(key)} is ignored."
                    )
            operation = openapi["paths"][path][method]
            parameters = operation.get("parameters", [])
            for parameter in parameters:
                for key in parameter:
                    if key not in ["name", "in", "required", "schema"] + [
                        "description"
                    ]:
                        warnings.warn(
                            f"{repr(filename)} OpenAPI paths {repr(path)} {repr(method)} parameters is ignored."
                        )
                if parameter["in"] not in ["path", "query", "header"]:
                    warnings.warn(
                        f"{repr(filename)} OpenAPI paths {repr(path)} {repr(method)} parameter {repr(parameter['name'])} in {repr(parameter['in'])} is ignored."
                    )
                if (
                    parameter["in"] == "header"
                    and parameter["schema"]["type"] != "string"
                ):
                    raise Exception(
                        f"{repr(filename)} OpenAPI paths {repr(path)} {repr(method)} parameter {repr(parameter['name'])} in header type {repr(parameter['schema']['type'])} is not supported, only string is allowed"
                    )
            if operation.get("requestBody"):
                for k in operation.get("requestBody"):
                    if k not in ["content", "required"]:
                        warnings.warn(
                            f"{repr(filename)} OpenAPI paths {repr(path)} {repr(method)} responseBody key {repr(k)} is ignored."
                        )
                assert operation.get("requestBody")["required"] == True, operation.get(
                    "requestBody"
                )["required"]
                assert list(operation.get("requestBody")["content"].keys()) == [
                    "application/json"
                ]
                assert list(
                    operation.get("requestBody")["content"]["application/json"].keys()
                ) == ["schema"], operation.get("requestBody")["content"][
                    "application/json"
                ]
                assert list(
                    operation.get("requestBody")["content"]["application/json"][
                        "schema"
                    ].keys()
                ) == ["$ref"], operation.get("requestBody")["content"][
                    "application/json"
                ][
                    "schema"
                ]

            for response_http_code in operation["responses"]:
                if response_http_code not in ["200", "201"]:
                    warnings.warn(
                        f"{repr(filename)} OpenAPI paths {repr(path)} {repr(method)} responses {repr(response_http_code)} is ignored."
                    )
                    continue
                for response_key in operation["responses"][response_http_code]:
                    if response_key not in ["content"] + ["description"]:
                        warnings.warn(
                            f"{repr(filename)} OpenAPI paths {repr(path)} {repr(method)} responses {repr(response_http_code)} {repr(response_key)} is ignored."
                        )
                        continue
                    if response_key == "content":
                        for response_content_type in operation["responses"][
                            response_http_code
                        ][response_key]:
                            if response_content_type not in ["application/json"]:
                                warnings.warn(
                                    f"{repr(filename)} OpenAPI paths {repr(path)} {repr(method)} responses {repr(response_http_code)} {repr(response_key)} {repr(response_content_type)} is ignored."
                                )
                                continue
                        assert (
                            "schema"
                            in operation["responses"][response_http_code]["content"][
                                "application/json"
                            ]
                        ), (
                            path,
                            method,
                            response_http_code,
                            response_key,
                            "application/json",
                            operation["responses"][response_http_code]["content"][
                                "application/json"
                            ],
                        )
                        if (
                            "$ref"
                            in operation["responses"][response_http_code]["content"][
                                "application/json"
                            ]["schema"]
                        ):
                            for schema_key in operation["responses"][
                                response_http_code
                            ]["content"]["application/json"]["schema"]:
                                if schema_key not in ["$ref"]:
                                    warnings.warn(
                                        f"{repr(filename)} OpenAPI paths {repr(path)} {repr(method)} responses {repr(response_http_code)} {repr(response_key)} application/json schema {repr(schema_key)} is ignored."
                                    )
                        else:
                            assert (
                                "array"
                                == operation["responses"][response_http_code][
                                    "content"
                                ]["application/json"]["schema"]["type"]
                            ), (
                                path,
                                method,
                                response_http_code,
                                response_key,
                                "application/json",
                                "schema",
                                operation["responses"][response_http_code]["content"][
                                    "application/json"
                                ]["schema"],
                            )
                            for schema_key in operation["responses"][
                                response_http_code
                            ]["content"]["application/json"]["schema"]:
                                if schema_key not in ["type", "items"]:
                                    warnings.warn(
                                        f"{repr(filename)} OpenAPI paths {repr(path)} {repr(method)} responses {repr(response_http_code)} {repr(response_key)} application/json schema {repr(schema_key)} is ignored."
                                    )
                            assert (
                                "$ref"
                                in operation["responses"][response_http_code][
                                    "content"
                                ]["application/json"]["schema"]["items"]
                            ), (
                                path,
                                method,
                                response_http_code,
                                response_key,
                                "application/json",
                                "schema",
                                "items",
                                operation["responses"][response_http_code]["content"][
                                    "application/json"
                                ]["schema"]["items"],
                            )
                            for items_key in operation["responses"][response_http_code][
                                "content"
                            ]["application/json"]["schema"]["items"]:
                                if items_key not in ["$ref"]:
                                    warnings.warn(
                                        f"{repr(filename)} OpenAPI paths {repr(path)} {repr(method)} responses {repr(response_http_code)} {repr(response_key)} application/json schema items {items_key} is ignored."
                                    )


jsonschema_types_to_python_types: dict[str, str] = {
    "string": "str",
    "integer": "int",
    "boolean": "bool",
}

jsonschema_types_to_python_example: dict[str, Any] = {
    "string": "'string'",
    "integer": 0,
    "boolean": True,
}


def print_handler(prefix, openapi):
    print()
    print()

    operations = []
    for path in openapi["paths"]:
        for method in openapi["paths"][path]:
            operations.append(openapi["paths"][path][method]["operationId"])

    operations_str = ", " + (
        ", ".join(
            # [
            #     f"{sd['name'].replace('-', '_').lower()}: str"
            #     for sd in openapi.get("securitySchemes", {}).values()
            # ]
            # +
            [f"{op}: Any" for op in operations]
        )
    )

    if openapi["components"].get("securitySchemes", {}):
        print(f"Security = TypedDict('Security', " + "{")
        print(f"    'verified_claims': dict[str, str],")
        for key, value in openapi["components"].get("securitySchemes").items():
            print(
                f"    '{key}': str",
            )
        print("})")
        print("")
        print("")

        # operations_str += ", security: Security"

    print(f"def make_{prefix}_handler(base_path: str" + operations_str + ") -> Any:")
    print(f"    def {prefix}_handler(http: Any) -> None:")
    print(
        "        assert http.request.path.startswith(base_path), (base_path, http.request.path)"
    )
    print(
        "        query = dict([(k, v[-1]) for k, v in parse_qs(http.request.query).items()])"
    )
    print(
        '        http.response.headers["Content-Type"] = "application/json; charset=utf-8"'
    )
    if openapi["components"].get("securitySchemes", {}):
        print(f"        security = Security(")
        print(f"            verified_claims=http.request.verified_claims,")
        for name, sd in openapi["components"].get("securitySchemes", {}).items():
            print(f"            {name}=http.request.headers['{sd['name'].lower()}'],")
        print(f"        )")

    print("        method = http.request.method.lower()")
    print("        openapi_path = http.request.path[len(base_path):]")

    operations_by_method: dict[str, Any] = {}
    for path in openapi["paths"]:
        for method in openapi["paths"][path]:
            if method not in operations_by_method:
                operations_by_method[method] = []
            operations_by_method[method].append((path, openapi["paths"][path][method]))
    for method in operations_by_method:
        print(f"        if method == '{method.lower()}':")
        for path, operation in operations_by_method[method]:
            path_param_strings = [
                "'" + p["name"] + "'"
                for p in operation.get("parameters", [])
                if p["in"] == "path"
            ]
            param_args = (
                [
                    p["name"]
                    + f'={operation["operationId"]}_params.get("'
                    + p["name"]
                    + '")'
                    for p in operation.get("parameters", [])
                    if p["in"] == "path"
                ]
                + [
                    p["name"] + '=query.get("' + p["name"] + '")'
                    for p in operation.get("parameters", [])
                    if p["in"] == "query" and p.get("required", False) is False
                ]
                + [
                    p["name"] + '=query["' + p["name"] + '"]'
                    for p in operation.get("parameters", [])
                    if p["in"] == "query" and p.get("required", False)
                ]
            )
            if openapi["components"].get("securitySchemes", {}):
                param_args.append("security=security")

            if path_param_strings:
                print(
                    f'            {operation["operationId"]}_params = path_matches(openapi_path, "{path}", ['
                    + ", ".join(path_param_strings)
                    + "])"
                )
                print(f'            if {operation["operationId"]}_params is not None:')
            else:
                print(f"            if openapi_path == '{path}':")
            print(
                f"                print('We are in the {operation['operationId']} handler.')"
            )
            if "requestBody" in operation:
                print(f"                try:")
                print(
                    f'                    body = json.loads(http.request.body.decode("utf8"))'
                )
                print(f"                    assert is_SubmitInput(body), body")
                print(f"                except Exception as e:")
                print(f"                    print(e)")
                print(
                    f'                    http.response.headers["Content-Type"] = "text/plain"'
                )
                print(f'                    http.response.status = "400 Invalid data"')
                print(f'                    http.response.body = b"Invalid data"')
                print(f"                else:")
                if param_args:
                    print(
                        f'                    http.response.body = {operation["operationId"]}(body, {", ".join(param_args)})'
                    )
                else:
                    print(
                        f'                    http.response.body = {operation["operationId"]}(body)'
                    )
            else:
                if param_args:
                    print(
                        f'                http.response.body = {operation["operationId"]}({", ".join(param_args)})'
                    )
                else:
                    print(
                        f'                http.response.body = {operation["operationId"]}()'
                    )
            print(f"                return")
    print("        http.response.status = '404 Not Found'")
    print("        http.response.body = 'Not Found'")
    print(
        "        http.response.headers = {'Content-Type': 'text/plain; charset=UTF-8'}"
    )
    print(f"    return {prefix}_handler")


def main(prefix, filename):
    jsonschemas: list[JsonschemaObject] = []
    operations: list[Operation] = []
    openapis = {}
    with open(filename, "r") as fp:
        try:
            openapi = json.loads(fp.read())
        except Exception as e:
            raise Exception(f"Failed to load {filename}. {e}")
        openapis[prefix] = openapi
        generate_warnings(filename, openapi)
        for path in openapi["paths"]:
            for method in openapi["paths"][path]:
                op = openapi["paths"][path][method]
                operations.append(
                    Operation(
                        path=path,
                        method=method,
                        operationId=op["operationId"],
                        parameters=op.get("parameters", []),
                        requestBody=op.get("requestBody"),
                        responses=op["responses"],
                    )
                )
        for title in openapi["components"]["schemas"].keys():
            jsonschema = openapi["components"]["schemas"][title]
            jsonschemas.append(
                JsonschemaObject(
                    title=title,
                    type=jsonschema["type"],
                    properties=jsonschema["properties"],
                    required=jsonschema.get("required"),
                    securitySchemes=openapi["components"].get("securitySchemes", {}),
                )
            )

    for jsonschema in jsonschemas:
        print()
        print()
        print(f"{jsonschema['title']} = TypedDict('{jsonschema['title']}', " + "{")
        for key, value in jsonschema["properties"].items():
            if key in (jsonschema.get("required") or []):
                if value["type"] == "array":
                    print(
                        f"    '{key}': list[\"{value['items']['$ref'][len('#/components/schemas/'):]}\"],"
                    )
                else:
                    print(
                        f"    '{key}': {jsonschema_types_to_python_types[value['type']]},"
                    )
            else:
                if "$ref" in value:
                    print(
                        f"    '{key}': NotRequired['{value['$ref'][len('#/components/schemas/'):]}'],"
                    )
                elif value["type"] == "object":
                    # This is a strange edge case where people abuse an empty property list with no required fields to create any object they like
                    if value == {"type": "object", "properties": {}}:
                        print(f"    '{key}': " + "NotRequired[dict[str,Any]],")
                    else:
                        raise Exception("Complex nesting not supported")
                elif value["type"] == "array":
                    if "$ref" in value["items"]:
                        print(
                            f"    '{key}': NotRequired[list[\"{value['items']['$ref'][len('#/components/schemas/'):]}\"]],"
                        )
                    else:
                        print(
                            f"    '{key}': NotRequired[list[{jsonschema_types_to_python_types[value['items']['type']]}]],"
                        )
                else:
                    # print(f'# {repr(value)}')
                    print(
                        f"    '{key}': NotRequired[{jsonschema_types_to_python_types[value['type']]}],"
                    )
        print("})")

        print()
        print()
        print(f"def generate_example_{jsonschema['title']}() -> {jsonschema['title']}:")
        print("    return {")
        for key, value in jsonschema["properties"].items():
            if "$ref" in value:
                print(
                    f"        '{key}': generate_example_{value['$ref'][len('#/components/schemas/'):]}(),"
                )
            else:
                if value["type"] == "array":
                    if "$ref" in value["items"]:
                        v = value["items"]["$ref"][len("#/components/schemas/") :]
                        if jsonschema["title"] == v:
                            warnings.warn(
                                f'Cannot generate a proper example for {repr(jsonschema["title"])}, because of the recursive nature of the definition'
                            )
                            print(f"        '{key}': [],")
                        else:
                            print(f"        '{key}': [generate_example_{v}()],")
                    else:
                        print(
                            f"        '{key}': [{jsonschema_types_to_python_example[value['items']['type']]}],"
                        )
                elif value["type"] == "object":
                    # This is a strange edge case where people abuse an empty property list with no required fields to create any object they like
                    if value == {"type": "object", "properties": {}}:
                        print(f"        '{key}': " + "{},")
                    else:
                        raise Exception("Complex nesting not supported")
                else:
                    print(
                        f"        '{key}': {jsonschema_types_to_python_example[value['type']]},"
                    )
        print("    }")
        print()
        print()
        print(
            f"def is_{jsonschema['title']}(value: dict[str, Any]) -> TypeGuard[{jsonschema['title']}]:"
        )
        print("    try:")
        for key, value in jsonschema["properties"].items():
            indent = ""
            if key not in (jsonschema.get("required") or []):
                print(f"        if '{key}' in value:")
                indent = "    "
            if "$ref" in value:
                print(
                    f"{indent}        assert is_{value['$ref'][len('#/components/schemas/'):]}(value['{key}']), value['{key}']"
                )
            elif value["type"] == "array":
                print(
                    f"{indent}        assert isinstance(value['{key}'], list), (value['{key}'], list)"
                )
                print(f"{indent}        for item in value['{key}']:")
                if "$ref" in value["items"]:
                    print(
                        f"{indent}            assert is_{value['items']['$ref'][len('#/components/schemas/') :]}(item), item"
                    )
                else:
                    print(
                        f"{indent}            assert isinstance(item, {jsonschema_types_to_python_types[value['items']['type']]}), item",
                    )
            elif value["type"] == "object":
                # This is a strange edge case where people abuse an empty property list with no required fields to create any object they like
                if value == {"type": "object", "properties": {}}:
                    print(
                        f"{indent}        assert isinstance(value['{key}'], dict), (value['{key}'], dict)"
                    )
                    print(f"{indent}        for k in value['{key}']:")
                    print(f"{indent}            assert isinstance(k, str)")
                else:
                    raise Exception("Complex nesting not supported")
            else:
                print(
                    f"{indent}        assert isinstance(value['{key}'], {jsonschema_types_to_python_types[value['type']]}), (value['{key}'], {jsonschema_types_to_python_types[value['type']]})"
                )
        print("        return True")
        print("    except (KeyError, AssertionError) as e:")
        print("        print(e)")
        print("        return False")

    for operation in operations:
        args: list[tuple[int, int, str, str]] = []
        query = []
        headers: list[tuple[str, bool]] = []
        url_replace_lines = [f"    url = base_url + '{operation['path']}'"]
        # Add in the security definitions first

        for security_scheme in jsonschema["securitySchemes"].values():
            arg = f"{security_scheme['name'].replace('-', '_').lower()}: str"
            args.append((0, len(args), arg, security_scheme["name"]))
            assert security_scheme["name"].lower() != "content-type", security_scheme[
                "name"
            ].lower()
            headers.append((security_scheme["name"], True))

        # if jsonschema["securitySchemes"]:
        #     args.append((0, len(args), 'security: Security', 'security: Security'))

        # for security_scheme in jsonschema["securitySchemes"].values():
        #     arg = f"{security_scheme['name'].replace('-', '_').lower()}: str"
        #     args.append((0, len(args), arg, security_scheme["name"]))
        #     assert security_scheme["name"].lower() != "content-type", security_scheme[
        #         "name"
        #     ].lower()
        #     headers.append((security_scheme["name"], True))
        # Prepare all the parameters
        for parameter in operation["parameters"]:
            if parameter.get("in") in ["path", "query", "header"]:
                if parameter.get("in") == "header":
                    arg = f"{parameter['name'].replace('-', '_').lower()}: {jsonschema_types_to_python_types[parameter['schema']['type']]}"
                else:
                    arg = f"{parameter['name'].replace('-', '_')}: {jsonschema_types_to_python_types[parameter['schema']['type']]}"
                if parameter.get("required") is not True:
                    arg += "|None=None"
                    args.append((1, len(args), arg, arg))
                else:
                    args.append((0, len(args), arg, arg))
                if parameter.get("in") == "path":
                    url_replace_lines.append(
                        "    url = url.replace('{"
                        + parameter["name"]
                        + "}', str("
                        + parameter["name"]
                        + "))"
                    )
                elif parameter.get("in") == "query":
                    if parameter.get("required") is True:
                        query.append(
                            f'    query["{parameter["name"]}"] = str({parameter["name"]})'
                        )
                    else:
                        query.append(f'    if {parameter["name"]} is not None:')
                        query.append(
                            f'        query["{parameter["name"]}"] = str({parameter["name"]})'
                        )
                else:
                    assert parameter["name"].lower() != "content-type", parameter[
                        "name"
                    ].lower()
                    if parameter.get("requried", False):
                        headers.append((parameter["name"], True))
                    else:
                        headers.append((parameter["name"], False))

        arg_strs: list[str] = [arg[2] for arg in sorted(args)]
        fn = f"def {prefix}_{operation['operationId']}(base_url: str"
        if operation.get("requestBody"):
            fn += f", request_data: {operation['requestBody']['content']['application/json']['schema']['$ref'][len('#/components/schemas/'):]}"
        if args:
            fn += ", " + (", ".join(arg_strs))

        def print_fetch():
            print("\n".join(url_replace_lines))
            if query:
                print("    query={}")
                print("\n".join(query))
                print("    url += '?' + urlencode(query)")

            print("    headers={'Content-Type': 'application/json' }")
            if headers:
                for name, required in headers:
                    if required:
                        print(
                            f"    headers['{name}'] = {name.replace('-', '_').lower()}"
                        )
                    else:
                        print(f"    if {name.replace('-', '_').lower()}:")
                        print(
                            f"        headers['{name}'] = {name.replace('-', '_').lower()}"
                        )

            if operation.get("requestBody"):
                print(
                    "    with urlopen(Request(url, data=json.dumps(request_data).encode(), method='"
                    + operation["method"].upper()
                    + "', headers=headers)) as response:"
                )
            else:
                print(
                    "    with urlopen(Request(url, method='"
                    + operation["method"].upper()
                    + "', headers=headers)) as response:"
                )
            print("        response_data = json.loads(response.read().decode())")
            # print("        print(response_data)")

        print()
        print()
        schema = None
        if "201" in operation["responses"]:
            schema = operation["responses"]["201"]["content"]["application/json"][
                "schema"
            ]
        else:
            schema = operation["responses"]["200"]["content"]["application/json"][
                "schema"
            ]
        if "$ref" in schema:
            t = schema["$ref"][len("#/components/schemas/") :]

            print(fn + f") -> {t}:")

            print_fetch()
            print(f"        assert is_{t}(response_data), response_data")
            # print(f'        TYPE_CHECKING and reveal_type(response_data)')
            print(f"        return response_data")
        else:
            type_ = schema["type"]
            assert type_ in ["array"]
            if type_ == "array":
                if "$ref" in schema["items"]:
                    t = schema["items"]["$ref"][len("#/components/schemas/") :]
                else:
                    t = jsonschema_types_to_python_types[schema["items"]["type"]]
                print(fn + f") -> list[{t}] :")
                print_fetch()
                print(f"        assert isinstance(response_data, list), response_data")
                print(f"        result: list[{t}] = []")
                print(f"        for item in response_data:")
                print(f"            assert is_{t}(item), item")
                print(f"            result.append(item)")
                # print(f'        TYPE_CHECKING and reveal_type(result)')
                print(f"        return result")

        # Now generate a sample handler
        print()
        print()

        fn = f"def example_handler_{prefix}_{operation['operationId']}("
        if operation.get("requestBody"):
            fn += f"request_data: {operation['requestBody']['content']['application/json']['schema']['$ref'][len('#/components/schemas/'):]}, "
        if args:
            fn += (", ".join(arg_strs)) + ", "
        if args or operation.get("requestBody"):
            fn = fn[:-2]
        if "$ref" in schema:
            t = schema["$ref"][len("#/components/schemas/") :]
            print(fn + f") -> {t}:")
            print(f"    return generate_example_{t}()")
        else:
            type_ = schema["type"]
            assert type_ in ["array"]
            if type_ == "array":
                if "$ref" in schema["items"]:
                    t = schema["items"]["$ref"][len("#/components/schemas/") :]
                else:
                    t = jsonschema_types_to_python_types[schema["items"]["type"]]
                print(fn + f") -> list[{t}] :")
                print(f"    return [generate_example_{t}()]")

    for prefix, openapi in openapis.items():
        print_handler(prefix, openapi)


if __name__ == "__main__":
    import sys

    print("from typing import TypedDict, TypeGuard, NotRequired, Any")
    print("from urllib.request import Request, urlopen")
    print("from urllib.parse import urlencode, parse_qs")
    print("import json")
    print()
    print()
    print(
        "def path_matches(http_path: str, openapi_path: str, path_params: list[str]) -> dict[str,str] | None:"
    )
    print("    params: dict[str, str] = {}")
    print("    if openapi_path.count('/') != http_path.count('/'):")
    print("        # print('Different counts:', openapi_path, http_path)")
    print("        return None")
    print("    path_params_left = path_params[:]")
    print("    http_path_parts = http_path.split('/')")
    print("    openapi_path_parts = openapi_path.split('/')")
    print("    # print(openapi_path_parts, http_path_parts, path_params_left)")
    print("    for i, part in enumerate(openapi_path_parts):")
    print("        if part.startswith('{') and part.endswith('}'):")
    print("            part = part[1:-1]")
    print("            if part in path_params:")
    # XXX What if two path values have different values? Poorly designed API?
    print("                params[part] = http_path_parts[i]")
    print("                http_path_parts[i] = '{' + part + '}'")
    print("            if part in path_params_left:")
    print("                path_params_left.pop(path_params_left.index(part))")
    print("    # print(openapi_path_parts, http_path_parts, path_params_left)")
    print("    if not path_params_left and http_path_parts == openapi_path_parts:")
    print("        return params")
    print("    return None")

    for filename in sys.argv[1:]:
        prefix = filename.replace(".json", "").replace("openapi-", "")
        main(prefix, filename)
