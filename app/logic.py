import os

from .typeddicts import ApiResponse, SubmitInput


def submit(input: SubmitInput) -> ApiResponse:
    if input["password"] != os.environ["PASSWORD"]:
        raise ValueError("Invalid password")
    else:
        return dict(success=True)
