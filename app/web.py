import os
import urllib.parse

from . import logic
from .template import Html, render


def home(http):
    body = Html("<ul>\n")
    for link, text in [
        ("/html", "HTML"),
        ("/str", "str"),
        ("/dict", "dict"),
        ("/bytes", "bytes (may download)"),
        ("/other", "Other (should raise error)"),
        ("/static/hello.png", "hello.png"),
        ("/submit", "Submit"),
    ]:
        body += Html('<li><a href="') + link + Html('">') + text + Html("</a></li>\n")
    body += Html("</ul>\n")
    http.response.body = render("Home", body)


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


def handle_static(http):
    filename = http.request.path[len("/static/") :]
    assert "/" not in filename
    assert ".." not in filename
    src = os.path.join(os.path.dirname(__file__), "static", filename + ".txt")
    assert os.path.dirname(os.path.abspath(os.path.normpath(src))) == os.path.join(
        os.path.dirname(os.path.abspath(os.path.normpath(__file__))), "static"
    )
    with open(src, "rb") as fp:
        type, content = fp.read().strip().split(b"\n")
        http.response.headers["content-type"] = type
        http.response.body = http.response.Base64(content)


def submit(http):
    if http.request.method == "post":
        q = urllib.parse.parse_qs(http.request.body.decode("utf8"))
        result = logic.submit_input(
            {"password": q["password"][0], "id": int(q["id"][0])}
        )
        assert result["success"]
        body = Html("<p>Submission in progress ...</p>\n")
        http.response.body = render("Success", body)
    else:
        body = Html('<form method="post">\n')
        body += Html('Password <input type="password" name="password">\n')
        body += Html('ID <input type="input" name="id">\n')
        body += Html('<input type="submit" value="Submit">\n')
        body += Html("</form>\n")
        http.response.body = render("Submit", body)


import tasks.driver


def progress(http):
    q = urllib.parse.parse_qs(http.request.query)
    header, task_list = tasks.driver.progress(q["workflow_id"][0])
    http.response.body = dict(header=header, task_list=task_list)
