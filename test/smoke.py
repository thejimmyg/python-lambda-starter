def test_web_html(lambda_url):
    import urllib.request

    with urllib.request.urlopen(lambda_url + "/html") as response:
        response_body = response.read()
        assert (
            response_body
            == b"<html><head><title>HTML</title></head><body><h1>He&lt;&gt;&amp;&quot;&#x27;llo!</h1><p>An HTML page with some escaping going on.</p></body></html>"
        ), response_body
        assert ("Content-Type", "text/html") in response.getheaders()
        assert ("Content-Length", "146") in response.getheaders()


def test_web_str(lambda_url):
    import urllib.request

    with urllib.request.urlopen(lambda_url + "/str") as response:
        response_body = response.read()
        assert response_body == b"Hello!", response_body
        assert ("Content-Type", "text/plain") in response.getheaders()
        assert ("Content-Length", "6") in response.getheaders()


def test_web_dict(lambda_url):
    import json
    import urllib.request

    with urllib.request.urlopen(lambda_url + "/dict") as response:
        response_body = response.read()
        assert response_body == b'{"hello": "world"}', response_body
        assert (
            "Content-Type",
            "application/json",
        ) in response.getheaders(), response.getheaders()
        assert ("Content-Length", "18") in response.getheaders()
        response_data = json.loads(response_body)
        assert response_data == {"hello": "world"}


def test_web_bytes(lambda_url):
    import urllib.request

    with urllib.request.urlopen(lambda_url + "/bytes") as response:
        response_body = response.read()
        assert response_body == b"some } { bytes", response_body
        assert ("Content-Type", "application/octet-stream") in response.getheaders()
        assert ("Content-Length", "14") in response.getheaders()


def test_web_other(lambda_url):
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(lambda_url + "/other") as response:
            response_body = response.read()
            raise Exception(
                "Was expecting a failure, but successfully read the body as: {repr(response_body)"
            )
    except urllib.error.HTTPError as e:
        # This is weird, do we want this behaviour?
        assert e.code in [500, 502], e.code
        response_body = e.read()
        if e.code == 502:
            assert e.reason == "Bad Gateway", e.reason
            assert response_body == b"Internal Server Error", response_body
            assert e.headers["Content-Type"] == "application/json", e.headers[
                "Content-Type"
            ]
            assert e.headers["Content-Length"] == "21", e.headers["Content-Length"]
        else:
            assert e.reason == "Internal Server Error", e.reason
            assert response_body in [
                b"A server error occurred.  Please contact the administrator.",
                b'{"message":"Internal Server Error"}',
            ], response_body
            assert e.headers["Content-Type"] in [
                "text/plain",
                "application/json",
            ], e.headers["Content-Type"]
            assert e.headers["Content-Length"] in ["59", "35"], e.headers[
                "Content-Length"
            ]


def test_web_static_hello_png(lambda_url):
    import os
    import urllib.request

    with urllib.request.urlopen(lambda_url + "/static/hello.png") as response:
        assert (
            "Content-Type",
            "image/png",
        ) in response.getheaders(), response.getheaders()
        size = os.stat("static/hello.png").st_size
        assert (
            "Content-Length",
            str(size),
        ) in response.getheaders(), response.getheaders()
        response_body = response.read()
        with open("static/hello.png", "rb") as fp:
            assert response_body == fp.read(), "Data differs"


def test_api_submit_input(lambda_url):
    import json
    import os
    import urllib.request
    import base64

    # No authorization header
    data = json.dumps({"password": os.environ["PASSWORD"], "id": 123}).encode("utf8")
    req = urllib.request.Request(lambda_url + "/api/submit_input", data=data)
    try:
        with urllib.request.urlopen(req) as response:
            response.read()
    except urllib.error.HTTPError as e:
        resp = e.read()
        assert resp == b'{"message":"Unauthorized"}', resp
    else:
        raise Exception("Expected a 401 to be raised")

    # Invalid authorization header
    data = json.dumps({"password": os.environ["PASSWORD"], "id": 123}).encode("utf8")
    req = urllib.request.Request(
        lambda_url + "/api/submit_input",
        data=data,
        headers={"authorization": "invalid"},
    )
    try:
        with urllib.request.urlopen(req) as response:
            response.read()
    except urllib.error.HTTPError as e:
        resp = e.read()
        assert resp == b'{"message":"Unauthorized"}', resp
    else:
        raise Exception("Expected a 401 to be raised")

    authorization = "start." + base64.urlsafe_b64encode(b"{}").decode("utf8") + ".end"

    if os.environ.get("DEV_MODE", "False").lower() == "true":
        # Valid header for tests
        data = json.dumps({"password": os.environ["PASSWORD"], "id": 123}).encode(
            "utf8"
        )
        req = urllib.request.Request(
            lambda_url + "/api/submit_input",
            data=data,
            headers={"authorization": authorization},
        )
        with urllib.request.urlopen(req) as response:
            assert (
                "Content-Type",
                "application/json",
            ) in response.getheaders(), response.getheaders()
            response_body = response.read()
            assert "workflow_id" in json.loads(
                response_body.decode("utf8")
            ), response_body

        # id is a string this time, not an integer
        data = json.dumps({"password": os.environ["PASSWORD"], "id": "123"}).encode(
            "utf8"
        )
        req = urllib.request.Request(
            lambda_url + "/api/submit_input",
            data=data,
            headers={"authorization": authorization},
        )
        try:
            with urllib.request.urlopen(req) as response:
                raise Exception(
                    "Expected the API call with the wrong type for id to fail, but it succeeded"
                )
        except urllib.error.HTTPError as e:
            assert e.code in [400], e.code
            response_body = e.read()
            assert e.reason in ["Bad Request", "Invalid data"], e.reason
            assert response_body == b"Invalid data", response_body
            assert e.headers["Content-Type"] == "text/plain", e.headers.get(
                "Content-Type"
            )
    else:
        print(
            "WARNING: Skipping API test because currently no way to generate a valid auth token for testing"
        )


def test_sdk_submit_input(lambda_url):
    import base64
    import os
    import urllib

    from app.typeddicts import SubmitInput, app_submit_input

    # Invalid authorization header
    try:
        result = app_submit_input(
            base_url=lambda_url + "/api",
            request_data=SubmitInput(password=os.environ["PASSWORD"], id=1),
            authorization="invalid_token",
        )
    except urllib.error.HTTPError as e:
        resp = e.read()
        assert resp == b'{"message":"Unauthorized"}', resp
    else:
        raise Exception("Expected a 401 to be raised")

    # With valid authorization header for tests
    if os.environ.get("DEV_MODE", "False").lower() == "true":
        authorization = (
            "start." + base64.urlsafe_b64encode(b"{}").decode("utf8") + ".end"
        )
        result = app_submit_input(
            base_url=lambda_url + "/api",
            request_data=SubmitInput(password=os.environ["PASSWORD"], id=1),
            authorization=authorization,
        )
        assert "workflow_id" in result, result
    else:
        print(
            "WARNING: Skipping API test because currently no way to generate a valid auth token for testing"
        )


if __name__ == "__main__":
    import sys

    lambda_url = sys.argv[1]

    test_web_html(lambda_url)
    print(".", end="")
    sys.stdout.flush()
    test_web_str(lambda_url)
    print(".", end="")
    sys.stdout.flush()
    test_web_dict(lambda_url)
    print(".", end="")
    sys.stdout.flush()
    test_web_bytes(lambda_url)
    print(".", end="")
    sys.stdout.flush()
    test_web_other(lambda_url)
    print(".", end="")
    sys.stdout.flush()
    test_web_static_hello_png(lambda_url)
    print(".", end="")
    sys.stdout.flush()
    test_api_submit_input(lambda_url)
    print(".", end="")
    test_sdk_submit_input(lambda_url)
    print(".", end="")
    sys.stdout.flush()
    print("\nSUCCESS")
