class NotFound(Exception):
    pass


class Remove:
    pass


from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class KvStore(Protocol):
    def render(self) -> str:
        ...

    def put(store, pk, data=None, sk="/", ttl=None) -> None:
        ...

    def patch(store, pk, data, sk="/", ttl=None) -> None:
        ...

    def delete(store, pk, sk="/") -> None:
        ...

    def iterate(
        store, pk, sk_start="/", limit=None, after=False, consistent=False
    ) -> tuple[Any, str | None]:
        ...

    def get(
        store, pk, sk="/", consistent=False
    ) -> tuple[dict[str, int | float | str], float | int | None]:
        ...
