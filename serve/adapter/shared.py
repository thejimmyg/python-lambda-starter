import dataclasses
from typing import Protocol, runtime_checkable


@runtime_checkable
class Renderable(Protocol):
    def render(self) -> str:
        ...


# This is for data that is already base64 encoded
class Base64:
    def __init__(self, data):
        self._data = data


@dataclasses.dataclass
class Request:
    path: str
    query: None | str
    headers: dict[str, str]
    method: str
    body: None | bytes


class RespondEarly(Exception):
    pass


@dataclasses.dataclass
class Response:
    status: str
    headers: dict[str, str]
    body: None | bytes | str | Renderable | dict | Base64
    RespondEarly: type[RespondEarly]
    Base64: type[Base64]


@dataclasses.dataclass
class Http:
    request: Request
    response: Response
    context: dict
