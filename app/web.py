from template import Html, render


def home(http):
    body = Html("<ul>\n")
    for link, text in [
        ("/html", "HTML"),
        ("/str", "str"),
        ("/dict", "dict"),
        ("/bytes", "bytes (may download)"),
        ("/other", "Other (should raise error)"),
        ("/static/hello.png", "hello.png"),
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
    with open("static_" + filename + ".txt", "rb") as fp:
        type, content = fp.read().strip().split(b"\n")
        http.response.headers["content-type"] = type
        http.response.body = http.response.Base64(content)
