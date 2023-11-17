from serve.adapter.wsgi.wsgi import start_server


def test_submit_input() -> None:
    from app.typeddicts import SubmitInput, app_submit_input

    result = app_submit_input(
        "http://localhost:8000/api",
        SubmitInput(id=1, password="password"),
        authorization="secret",
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

    def submit_input(input_: SubmitInput, validated_security) -> SubmitInputResponse:
        return generate_example_SubmitInputResponse()

    def progress(workflow_id: str, validated_security) -> ProgressResponse:
        return generate_example_ProgressResponse()

    def validate_security(http, authorization):
        if authorization == "secret":
            return True
        raise http.response.RespondEarly("No authenticated")

    start_server(
        {
            "/api": make_app_handler(
                "/api",
                submit_input=submit_input,
                progress=progress,
                validate_security=validate_security,
            )
        }
    )


if __name__ == "__main__":
    main()
