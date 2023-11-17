from . import operation, web
from .typeddicts import make_app_handler


def validate_security(http, authorization):
    if authorization == "secret":
        return True
    raise http.response.RespondEarly("No authenticated")


app_handler = make_app_handler(
    "/api",
    submit_input=operation.submit_input,
    progress=operation.progress,
    validate_security=validate_security,
)


handle_static = web.make_handle_static("/static/")
handle_favicon = web.make_handle_static("/")


def app(http):
    if http.request.path == "/":
        web.home(http)
    elif http.request.path == "/favicon.ico":
        handle_favicon(http)
    elif http.request.path == "/test":
        web.test(http)
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
        handle_static(http)
    elif http.request.path.startswith("/submit"):
        web.submit(http)
    elif http.request.path.startswith("/progress"):
        web.progress(http)
    elif http.request.path.startswith("/api"):
        app_handler(http)
    else:
        http.response.headers["content-type"] = "text/plain"
        http.response.status = "404 Not Found"
        http.response.body = b"Not Found"
