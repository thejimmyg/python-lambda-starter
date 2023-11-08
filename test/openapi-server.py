from serve.adapter.wsgi import start_server


def test_submit_input() -> None:
    from app.typeddicts import SubmitInput, app_submit_input

    result = app_submit_input(
        "http://localhost:8000/api", SubmitInput(id=1, password="password")
    )
    assert result == {"success": True}, result


def main() -> None:
    from app.typeddicts import (
        ApiResponse,
        SubmitInput,
        generate_example_ApiResponse,
        make_app_handler,
    )

    def submit_input(input_: SubmitInput) -> ApiResponse:
        return generate_example_ApiResponse()

    start_server({"/api": make_app_handler("/api", submit_input=submit_input)})


if __name__ == "__main__":
    main()
