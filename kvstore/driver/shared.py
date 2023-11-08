class NotFoundInStoreDriver(Exception):
    pass


from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class KvStore(Protocol):
    def render(self) -> str:
        ...

    def put(store, pk, data, sk="/", ttl=None) -> None:
        ...

    def patch(store, pk, data, sk="/", ttl=None) -> None:
        ...

    def delete(store, pk, sk="/") -> None:
        ...

    def iterate(
        store, pk, sk_start="/", limit=None, consistent=False
    ) -> tuple[Any, str | None]:
        ...
