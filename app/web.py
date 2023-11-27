import os
import urllib.parse

from . import operation
from .template import Html, Test, Base, Main
from .typeddicts import AppSecurity
import tasks.driver


def test(http):
    http.response.body = Test("Home")


def test_html(http):
    http.response.body = (
        Html("<html><head><title>HTML</title></head><body><h1>")
        + "He<>&\"'llo!"
        + Html("</h1><p>")
        + "An HTML page with some escaping going on."
        + Html("</p></body></html>")
    )


def test_str(http):
    http.response.body = "Hello!"


def test_dict(http):
    http.response.body = {"hello": "world"}


def test_bytes(http):
    # Bytes responses must set their content type
    http.response.headers["content-type"] = "application/octet-stream"
    http.response.body = b"some } { bytes"


def test_other(http):
    class Other:
        pass

    http.response.body = Other()


def make_handle_static(base_path):
    assert base_path.endswith(
        "/"
    ), f"Base path should always end in /. You have specified: {repr(base_path)}"

    def handle_static(http):
        filename = http.request.path[len(base_path) :]
        assert "/" not in filename
        assert ".." not in filename
        src = os.path.join(os.path.dirname(__file__), "static", filename + ".txt")
        assert os.path.dirname(os.path.abspath(os.path.normpath(src))) == os.path.join(
            os.path.dirname(os.path.abspath(os.path.normpath(__file__))), "static"
        )
        with open(src, "r") as fp:
            parts = fp.read().strip().split("\n")
            if len(parts) == 1:
                type_ = parts[0]
                content = ""
            else:
                type_, content = parts
            http.response.headers["content-type"] = type_
            http.response.body = http.response.Base64(content)

    return handle_static


def submit(http):
    if http.request.method == "post":
        q = urllib.parse.parse_qs(http.request.body.decode("utf8"))
        result = operation.submit_input(
            {"password": q["password"][0], "id": int(q["id"][0])},
            # Pretending we have authorized
            security=AppSecurity(access_token="", verified_claims={}),
        )
        body = (
            Html('<p>Submission in progress ... <a href="/progress?workflow_id=')
            + urllib.parse.quote(result["workflow_id"])
            + Html('">Check Progress</a>.</p>\n')
        )
        http.response.body = Base("Success", body)
    else:
        body = Html('<form method="post">\n')
        body += Html('Password <input type="password" name="password">\n')
        body += Html('ID <input type="input" name="id">\n')
        body += Html('<input type="submit" value="Submit">\n')
        body += Html("</form>\n")
        http.response.body = Base("Submit", body)


import json


def progress(http):
    q = urllib.parse.parse_qs(http.request.query)
    workflow_id = q["workflow_id"][0]
    progress_response = operation.progress(
        workflow_id=workflow_id,
        # Pretending we have authorized
        security=AppSecurity(access_token="", verified_claims={}),
    )
    # Can determine the status as follows:
    statuses = {
        "RUNNING": "Running",
        "SUCCEEDED": "Succeeded",
        "FAILED": "Failed",
        "TIMED_OUT": "Timed Out",
        "ABORTED": "Aborted",
        "PENDING_REDRIVE": "Pending Restart",
    }
    status = None
    if "begin" in progress_response:
        status = "RUNNING"
        execution_status = tasks.driver.get_execution_status(
            progress_response["execution"]
        )
        if execution_status in statuses:
            status = statuses[execution_status]
    if "end" in progress_response:
        status = "SUCCEEDED"
    if "status" in progress_response and "status" == "FAILED":
        status = "FAILED"
    http.response.body = Main("Progress", main=json.dumps((status, progress_response)))


def home(http):
    http.response.body = Main(
        title="Home",
        main=Html("""<p>This is the homepage.</p>"""),
    )
