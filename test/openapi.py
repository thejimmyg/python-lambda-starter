from typing import Any


def start_server(handlers: dict[str, Any]) -> None:
    import json
    from dataclasses import dataclass
    from typing import Any

    @dataclass
    class Request:
        path: str
        query: None | str
        headers: dict[str, str]
        method: str
        body: None | bytes

    @dataclass
    class Response:
        status: str
        headers: dict[str, str]
        body: None | bytes

    @dataclass
    class Http:
        request: Request
        response: Response

    from wsgiref.simple_server import make_server

    def app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
        method = environ["REQUEST_METHOD"].lower()
        path = environ["PATH_INFO"]
        handler = None
        for handler_path in handlers:
            if path.startswith(handler_path + "/"):
                handler = handlers[handler_path]
                # path = path[len(handler_path + '/') :]
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
        http = Http(
            request=Request(
                path=path,
                query=query or None,
                headers=request_headers,
                method=method.lower(),
                body=request_body,
            ),
            response=Response(
                body=None,
                status="200 OK",
                headers={"Content-type": "application/json; charset=utf-8"},
            ),
        )
        handler(http)
        start_response(http.response.status, list(http.response.headers.items()))
        return [json.dumps(http.response.body).encode()]

    with make_server("", 8000, app) as httpd:
        print("Serving on port 8000...")
        httpd.serve_forever()


def test_submit_input() -> None:
    from app.typeddicts import SubmitInput, app_submit_input

    result = app_submit_input(
        "http://localhost:8000/api", SubmitInput(id=1, password="password")
    )
    assert result == {"success": True}, result


def main() -> None:
    import multiprocessing
    import time

    from app.typeddicts import (
        ApiResponse,
        SubmitInput,
        generate_example_ApiResponse,
        make_app_handler,
    )

    def submit_input(input_: SubmitInput) -> ApiResponse:
        return generate_example_ApiResponse()

    proc = multiprocessing.Process(
        target=start_server,
        args=({"/api": make_app_handler("/api", submit_input=submit_input)},),
    )
    proc.start()
    time.sleep(1)
    try:
        test_submit_input()
        print(".", end="")
    except Exception:
        print("\nFAILED\n")
        raise
    else:
        print("\nSUCCESS")
    finally:
        # Send a SIGTERM
        proc.terminate()


if __name__ == "__main__":
    main()
