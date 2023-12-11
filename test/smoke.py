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


def test_web_submit(lambda_url):
    import os
    import urllib.parse
    import urllib.request

    # No authorization header
    data = urllib.parse.urlencode(
        {"password": os.environ["PASSWORD"], "id": 123}
    ).encode("utf8")
    req = urllib.request.Request(lambda_url + "/submit", data=data)
    with urllib.request.urlopen(req) as response:
        response_body = response.read()
        assert b"<p>Submission in progress ... " in response_body, response_body
        # <a href="/progress?workflow_id=2023-11-23T10%3A56%3A29.867590/023a79c7-4999-4816-91d5-831eb9226d90">Check Progress</a>
        assert b"/progress?workflow_id=" in response_body, response_body
        assert b"Check Progress" in response_body, response_body


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
    import time
    import urllib

    from app.typeddicts import SubmitInput, app_submit_input, app_progress

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
        progress = app_progress(
            base_url=lambda_url + "/api",
            workflow_id=result["workflow_id"],
            authorization=authorization,
        )
        assert set(progress.keys()) == set(
            ["num_tasks", "begin", "begin_uid", "execution"]
        ), progress.keys()
        assert progress["num_tasks"] == 2, progress
        # XXX What about the state?

        print("Waiting 1 second for the first task to start")
        time.sleep(1)
        progress = app_progress(
            base_url=lambda_url + "/api",
            workflow_id=result["workflow_id"],
            authorization=authorization,
        )
        assert sorted(list(progress.keys())) == sorted(
            ["num_tasks", "begin", "begin_uid", "tasks", "banana", "execution"]
        ), progress.keys()
        assert dict(progress)["banana"] == "fruit", dict(progress)["banana"]
        assert progress["num_tasks"] == 2, progress["num_tasks"]
        assert len(progress["tasks"]) == 1, progress["tasks"]
        assert progress["tasks"][0]["task"] == 1
        assert progress["tasks"][0]["remaining"] == 1
        # This is the state we added in register_begin()
        assert dict(progress["tasks"][0])["starting"] == 1
        assert sorted(list(progress["tasks"][0].keys())) == sorted(
            list(
                [
                    "task",
                    "remaining",
                    "begin",
                    "starting",
                    "begin_uid",
                    "correctly_escaped_html_status_message",
                ]
            )
        ), progress["tasks"][0]

        print("Waiting 3.5 seconds for the first task to complete")
        time.sleep(3.5)
        progress = app_progress(
            base_url=lambda_url + "/api",
            workflow_id=result["workflow_id"],
            authorization=authorization,
        )
        assert sorted(list(progress.keys())) == sorted(
            ["banana", "num_tasks", "begin", "tasks", "begin_uid", "execution"]
        ), progress.keys()
        assert progress["num_tasks"] == 2, progress["num_tasks"]
        assert len(progress["tasks"]) == 2, progress["tasks"]
        assert progress["tasks"][0]["task"] == 2
        assert progress["tasks"][0]["remaining"] == 0
        assert dict(progress["tasks"][0])["starting"] == 2
        assert progress["tasks"][1]["task"] == 1
        assert progress["tasks"][1]["remaining"] == 1
        assert dict(progress["tasks"][1])["starting"] == 1
        assert dict(progress["tasks"][1])["ending"] == 1
        assert sorted(list(progress["tasks"][0].keys())) == sorted(
            list(
                [
                    "task",
                    "remaining",
                    "begin",
                    "begin_uid",
                    "starting",
                    "correctly_escaped_html_status_message",
                ]
            )
        ), progress["tasks"][0]
        # They are in reverse order, so it is this task that has finished
        assert sorted(list(progress["tasks"][1].keys())) == sorted(
            list(
                [
                    "task",
                    "remaining",
                    "begin",
                    "end",
                    "begin_uid",
                    "end_uid",
                    "starting",
                    "ending",
                    "correctly_escaped_html_status_message",
                ]
            )
        ), progress["tasks"][1]

        print("Waiting another 3 seconds for the workflow to complete")
        time.sleep(3)
        progress = app_progress(
            base_url=lambda_url + "/api",
            workflow_id=result["workflow_id"],
            authorization=authorization,
        )
        assert sorted(list(progress.keys())) == sorted(
            [
                "num_tasks",
                "begin",
                "begin_uid",
                "banana",
                "end",
                "end_uid",
                "tasks",
                "execution",
                "status",
            ]
        ), progress.keys()

        assert progress["num_tasks"] == 2, progress["num_tasks"]
        assert len(progress["tasks"]) == 2, progress["tasks"]
        assert progress["tasks"][0]["task"] == 2
        assert progress["tasks"][0]["remaining"] == 0
        assert dict(progress["tasks"][0])["starting"] == 2
        assert dict(progress["tasks"][0])["ending"] == 2
        assert progress["tasks"][1]["task"] == 1
        assert progress["tasks"][1]["remaining"] == 1
        assert dict(progress["tasks"][1])["starting"] == 1
        assert dict(progress["tasks"][1])["ending"] == 1
        for task in progress["tasks"]:
            assert sorted(list(task.keys())) == sorted(
                list(
                    [
                        "task",
                        "remaining",
                        "begin",
                        "end",
                        "begin_uid",
                        "end_uid",
                        "starting",
                        "ending",
                        "correctly_escaped_html_status_message",
                    ]
                )
            ), task
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
    test_web_submit(lambda_url)
    print(".", end="")
    sys.stdout.flush()
    test_api_submit_input(lambda_url)
    print(".", end="")
    sys.stdout.flush()
    test_sdk_submit_input(lambda_url)
    print(".", end="")
    sys.stdout.flush()
    print("\nSUCCESS")
