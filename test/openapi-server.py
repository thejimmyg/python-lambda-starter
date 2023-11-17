from serve.adapter.wsgi.wsgi import start_server


def test_submit_input() -> None:
    from app.typeddicts import SubmitInput, app_submit_input

    result = app_submit_input(
        "http://localhost:8000/api", SubmitInput(id=1, password="password")
    )
    assert result == {"success": True}, result


def main() -> None:
    from app.typeddicts import (
        SubmitInputResponse,
        SubmitInput,
        ProgressResponse,
        generate_example_ProgressResponse,
        generate_example_SubmitInputResponse,
        make_app_handler,
    )

    def submit_input(input_: SubmitInput) -> SubmitInputResponse:
        return generate_example_SubmitInputResponse()

    def progress(workflow_id: str) -> ProgressResponse:
        return generate_example_ProgressResponse()

    start_server(
        {"/api": make_app_handler("/api", submit_input=submit_input, progress=progress)}
    )


if __name__ == "__main__":
    main()
