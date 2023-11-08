import base64
import json

import app.app

from .shared import Base64, Http, Renderable, Request, RespondEarly, Response


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
            request_body = event["body"].encode("utf8")
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
        app.app.app(http)
    except RespondEarly:
        pass
    headers = {}
    for k, v in http.response.headers.items():
        k = "-".join([part.lower().capitalize() for part in k.split("-")])
        headers[k] = v
    # Don't need a except: block here because Lambda returns a 502 bad gateway on error and logs to cloudwatch anyway, and API gateway returns a 500.
    if isinstance(http.response.body, bytes):
        assert "Content-Type" in headers, "No content-type set for bytes type response"
        return {
            "statusCode": int(http.response.status.split(" ")[0]),
            "headers": headers,
            "body": base64.b64encode(http.response.body),
            "isBase64Encoded": True,
        }
    elif isinstance(http.response.body, Base64):
        assert "Content-Type" in headers, "No content-type set for bytes type response"
        return {
            "statusCode": int(http.response.status.split(" ")[0]),
            "headers": headers,
            # Don't need to encode the content again, already base64
            "body": http.response.body._data,
            "isBase64Encoded": True,
        }
    # Checks anything with a render() method, regardless of the args.
    elif isinstance(http.response.body, Renderable):
        # Lambda adds the content length
        headers["Content-Type"] = "text/html"
        return {
            "statusCode": int(http.response.status.split(" ")[0]),
            "headers": headers,
            "body": http.response.body.render(),
        }
    elif isinstance(http.response.body, dict):
        # Lambda adds the correct content type and content length headers
        # for JSON, API Gateway does not
        headers["Content-Type"] = "application/json"
        return {
            "statusCode": int(http.response.status.split(" ")[0]),
            "headers": headers,
            # Lambda function URL encodes the JSON, API Gateway does not.
            "body": json.dumps(http.response.body),
        }
    elif isinstance(http.response.body, str):
        headers["Content-Type"] = "text/plain"
        return {
            "statusCode": int(http.response.status.split(" ")[0]),
            "headers": headers,
            "body": http.response.body,
        }
    else:
        raise Exception(f"Unknown resposne type: {type(http.response.body)}")
