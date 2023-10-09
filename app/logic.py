import os
from dataclasses import dataclass


@dataclass
class SubmitInput:
    password: str
    id: int


@dataclass
class Response:
    success: bool


def submit(input: SubmitInput) -> Response:
    if input.password != os.environ["PASSWORD"]:
        raise ValueError("Invalid password")
    else:
        return Response(success=True)
