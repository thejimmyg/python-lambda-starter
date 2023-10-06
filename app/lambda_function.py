import base64
import dataclasses
import json

import template

import app


class Base64:
    def __init__(self, data):
        self._data = data


@dataclasses.dataclass
class Request:
    path: str
    query: None | str
    headers: dict
    method: str
    body: None | bytes


class RespondEarly(Exception):
    pass


@dataclasses.dataclass
class Response:
    status: str
    headers: dict
    body: None | bytes | str | template.Html | dict | Base64
    respond_early: RespondEarly
    Base64: Base64


@dataclasses.dataclass
class Http:
    request: Request
    response: Response
    context: dict


def lambda_handler(event, context):
    method = event["requestContext"]["http"]["method"].lower()
    path = event["rawPath"]
    query = event["rawQueryString"]
    request_headers = event["headers"]
    request_body = None
    if event.get("body"):
        if event.get("isBase64Encoded"):
            request_body = base64.b64decode(event["body"])
        else:
            request_body = event["body"]
    request = Request(
        path=path,
        query=query or None,
        headers=request_headers,
        method=method.lower(),
        body=request_body,
    )
    response = Response(
        status="200 OK",
        headers={},
        body=None,
        respond_early=RespondEarly,
        Base64=Base64,
    )
    http = Http(
        request=request, response=response, context=dict(uid=context.aws_request_id)
    )
    try:
        app.app(http)
    except RespondEarly:
        pass
    # Don't need a except: block here because Lambda returns a 502 bad gateway on error and logs to cloudwatch anyway, and API gateway returns a 500.
    response_body_type = type(http.response.body)
    if response_body_type is bytes:
        assert (
            "content-type" in http.response.headers
        ), "No content-type set for bytes type response"
        return {
            "statusCode": int(http.response.status.split(" ")[0]),
            "headers": http.response.headers,
            "body": base64.b64encode(http.response.body),
            "isBase64Encoded": True,
        }
    elif response_body_type is Base64:
        assert (
            "content-type" in http.response.headers
        ), "No content-type set for bytes type response"
        return {
            "statusCode": int(http.response.status.split(" ")[0]),
            "headers": http.response.headers,
            # Don't need to encode the content again, already base64
            "body": http.response.body._data,
            "isBase64Encoded": True,
        }
    elif response_body_type is template.Html:
        # Lambda adds the content length
        http.response.headers["content-type"] = "text/html"
        return {
            "statusCode": int(http.response.status.split(" ")[0]),
            "headers": http.response.headers,
            "body": http.response.body.render(),
        }
    elif response_body_type is dict:
        # Lambda adds the correct content type and content length headers
        # for JSON, API Gateway does not
        http.response.headers["content-type"] = "application/json"
        return {
            "statusCode": int(http.response.status.split(" ")[0]),
            "headers": http.response.headers,
            # Lambda function URL encodes the JSON, API Gateway does not.
            "body": json.dumps(http.response.body),
        }
    elif response_body_type is str:
        http.response.headers["content-type"] = "text/plain"
        return {
            "statusCode": int(http.response.status.split(" ")[0]),
            "headers": http.response.headers,
            "body": http.response.body,
        }
    else:
        raise Exception(f"Unknown resposne type: {type(http.response.body)}")
