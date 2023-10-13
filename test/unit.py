def test_template_render_home():
    from app.template import render_home

    html = render_home().render()
    expected = '<!DOCTYPE html>\n<html lang="en"><head><title>Home</title><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta charset="UTF-8"></head><body><h1>Home</h1><ul>\n<li><a href="/html">HTML</a></li>\n<li><a href="/str">str</a></li>\n<li><a href="/dict">dict</a></li>\n<li><a href="/bytes">bytes</a></li>\n<li><a href="/other">Other (should raise error)</a></li>\n</ul>\n</body></html>'
    assert html == expected, repr((html, expected))


def test_web_submit():
    from app.app import app
    from app.lambda_function import Base64, Http, Request, RespondEarly, Response
    from app.template import Html

    http = Http(
        request=Request(
            path="/submit",
            query="",
            headers={},
            method="get",
            body=b"",
        ),
        response=Response(
            status="200 OK",
            headers={},
            body=None,
            respond_early=RespondEarly,
            Base64=Base64,
        ),
        context=dict(uid="123"),
    )
    app(http)
    assert isinstance(http.response.body, Html)
    body = http.response.body.render()
    assert "<form" in body, body

    http = Http(
        request=Request(
            path="/submit",
            query="",
            headers={},
            method="post",
            body=b"password=" + os.environ["PASSWORD"].encode("utf8") + b"&id=1",
        ),
        response=Response(
            status="200 OK",
            headers={},
            body=None,
            respond_early=RespondEarly,
            Base64=Base64,
        ),
        context=dict(uid="123"),
    )
    app(http)
    assert isinstance(http.response.body, Html)
    body = http.response.body.render()
    assert "Success" in body, body


def test_types():
    from app.typeddicts import is_apiresponse

    # Invalid case
    try:
        r: dict = {}
        assert is_apiresponse(r)
    except AssertionError:
        pass
    else:
        assert r["success"]
        raise Exception("Failed to raise assertion")
    # Valid case
    s: dict = {"success": True}
    assert is_apiresponse(s)
    assert s["success"]


def test_api():
    import json

    from app import typeddicts
    from app.app import app
    from app.lambda_function import Base64, Http, Request, RespondEarly, Response

    http = Http(
        request=Request(
            path="/api",
            query="",
            headers={},
            method="post",
            body=json.dumps({"id": 123, "password": os.environ["PASSWORD"]}).encode(
                "utf8"
            ),
        ),
        response=Response(
            status="200 OK",
            headers={},
            body=None,
            respond_early=RespondEarly,
            Base64=Base64,
        ),
        context=dict(uid="123"),
    )
    app(http)
    assert (
        isinstance(http.response.body, dict)
        and typeddicts.is_apiresponse(http.response.body)
        and http.response.body == {"success": True}
    ), http.response.body


if __name__ == "__main__":
    import os
    import sys

    test_types()
    print(".", end="")
    sys.stdout.flush()

    test_template_render_home()
    print(".", end="")
    sys.stdout.flush()

    test_web_submit()
    print(".", end="")
    sys.stdout.flush()

    test_api()
    print(".", end="")
    sys.stdout.flush()

    print("\nSUCCESS")
