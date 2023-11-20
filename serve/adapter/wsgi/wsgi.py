import base64
import os
import json
import uuid
from socketserver import ThreadingMixIn
from typing import Any
from wsgiref.simple_server import WSGIServer, make_server

from ..shared import Base64, Http, Renderable, Request, RespondEarly, Response


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    # This doesn't correctly set wsgi.multithread, but I can't find an easy way to fix that. Other servers will behave better.
    pass


def start_server(handlers: dict[str, Any], port=8000, host="localhost") -> None:
    def app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
        method = environ["REQUEST_METHOD"].lower()
        path = environ["PATH_INFO"]
        handler = None
        for handler_path in handlers:
            if path.startswith(handler_path + "/"):
                handler = handlers[handler_path]
                break
        assert (
            handler is not None
        ), f"No valid handler out of {repr(handlers.keys())} found for the path {repr(path)}."
        query = environ.get("QUERY_STRING", "")
        request_headers: dict[str, str] = {}
        for key in environ:
            if key.startswith("HTTP_"):
                request_header_name = key[5:].lower()
                if request_header_name in request_headers:
                    request_headers[request_header_name] += "; " + environ[key]
                else:
                    request_headers[request_header_name] = environ[key]
        request_body = None
        if "wsgi.input" in environ and environ.get("CONTENT_LENGTH"):
            request_body = environ["wsgi.input"].read(int(environ["CONTENT_LENGTH"]))
        verified_claims = None
        if "authorization" in request_headers:
            assert os.environ.get("DEV_MODE", "false").lower() == "true"
            print("WARNING: In dev mode, not verifying the claims, just claiming to.")
            token = request_headers["authorization"]
            if " " in token:
                token = token.split(" ")[-1]
            s = token.split(".")[1].encode("utf8")
            verified_claims = json.loads(
                base64.urlsafe_b64decode(s + (b"=" * (4 - len(s) % 4)))
            )
        http = Http(
            request=Request(
                path=path,
                query=query or None,
                headers=request_headers,
                method=method.lower(),
                body=request_body,
                verified_claims=verified_claims,
            ),
            response=Response(
                body=None,
                status="200 OK",
                headers={},
                RespondEarly=RespondEarly,
                Base64=Base64,
            ),
            context=dict(uid=str(uuid.uuid4())),
        )
        if handler(http) is not None:
            print(
                "Warning, app should not return a response. Did you return instead of setting http.response.body?"
            )
        headers = {}
        for k, v in http.response.headers.items():
            k = "-".join([part.lower().capitalize() for part in k.split("-")])
            headers[k] = v
        if isinstance(http.response.body, bytes):
            assert (
                "Content-Type" in headers
            ), "No content-type set for bytes type response"
            headers["Content-Length"] = str(len(http.response.body))
            start_response(http.response.status, list(headers.items()))
            return [http.response.body]
        elif isinstance(http.response.body, Base64):
            assert (
                "Content-Type" in headers
            ), "No content-type set for bytes type response"
            body = base64.b64decode(http.response.body._data)
            headers["Content-Length"] = str(len(body))
            start_response(http.response.status, list(headers.items()))
            return [body]
        # Checks anything with a render() method, regardless of the args.
        elif isinstance(http.response.body, Renderable):
            body = http.response.body.render().encode("utf8")
            headers["Content-Type"] = "text/html"
            headers["Content-Length"] = str(len(body))
            start_response(http.response.status, list(headers.items()))
            return [body]
        elif isinstance(http.response.body, (list, dict)):
            body = json.dumps(http.response.body).encode("utf8")
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(len(body))
            start_response(http.response.status, list(headers.items()))
            return [body]
        elif isinstance(http.response.body, str):
            body = http.response.body.encode("utf8")
            headers["Content-Type"] = "text/plain"
            headers["Content-Length"] = str(len(body))
            start_response(http.response.status, list(headers.items()))
            return [body]
        else:
            raise Exception(f"Unknown response type: {repr(http.response.body)}")

    with make_server(host, port, app, ThreadingWSGIServer) as httpd:
        print(f"Serving on host {repr(host)} port {repr(port)} ...")
        httpd.serve_forever()
