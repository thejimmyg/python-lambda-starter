import web


def app(http):
    # Dispatch to handlers here:
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
    else:
        http.response.headers["content-type"] = "text/plain"
        http.response.status = "404 Not Found"
        http.response.body = b"404 Not Found"
