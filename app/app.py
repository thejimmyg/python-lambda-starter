import json

from . import logic, typeddicts, web


def app(http):
    if http.request.path == "/":
        web.home(http)
    elif http.request.path == "/bytes":
        web.test_bytes(http)
    elif http.request.path == "/html":
        web.test_html(http)
    elif http.request.path == "/str":
        web.test_str(http)
    elif http.request.path == "/dict":
        web.test_dict(http)
    elif http.request.path == "/other":
        web.test_other(http)
    elif http.request.path.startswith("/static/"):
        web.handle_static(http)
    elif http.request.path.startswith("/submit"):
        web.submit(http)
    elif http.request.path.startswith("/api"):
        if http.request.method == "post":
            data = json.loads(http.request.body.decode("utf8"))
            if typeddicts.is_submitinput(data):
                http.response.body = logic.submit(data)
            else:
                http.response.headers["content-type"] = "text/plain"
                http.response.status = "400 Invalid data"
                http.response.body = b"Invalid data"
        else:
            http.response.headers["content-type"] = "text/plain"
            http.response.status = "405 Bad Method"
            http.response.body = b"Bad Method"
    else:
        http.response.headers["content-type"] = "text/plain"
        http.response.status = "404 Not Found"
        http.response.body = b"Not Found"
