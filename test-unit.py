def test_template_render_home():
    from template import render_home

    html = render_home().render()
    expected = '<!DOCTYPE html>\n<html lang="en"><head><title>Home</title><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta charset="UTF-8"></head><body><h1>Home</h1><ul>\n<li><a href="/html">HTML</a></li>\n<li><a href="/str">str</a></li>\n<li><a href="/dict">dict</a></li>\n<li><a href="/bytes">bytes</a></li>\n<li><a href="/other">Other (should raise error)</a></li>\n</ul>\n</body></html>'
    assert html == expected, repr((html, expected))


def test_web_submit():
    from lambda_function import Base64, Http, Request, RespondEarly, Response
    from template import Html

    import app

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
    app.app(http)
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
    app.app(http)
    assert isinstance(http.response.body, Html)
    body = http.response.body.render()
    assert "Success" in body, body


if __name__ == "__main__":
    import os
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

    test_template_render_home()
    print(".", end="")
    sys.stdout.flush()

    test_web_submit()
    print(".", end="")
    sys.stdout.flush()
    print("\nSUCCESS")
