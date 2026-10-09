from types import TracebackType
from typing import Protocol, Self

from ai_backend_lab.application.ports.repositories import OrderRepository


class UnitOfWork(Protocol):
    orders: OrderRepository

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
