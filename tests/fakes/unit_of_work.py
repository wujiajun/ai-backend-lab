from types import TracebackType
from typing import Self

from ai_backend_lab.application.ports.repositories import OrderRepository


class FakeUnitOfWork:
    def __init__(
        self,
        orders: OrderRepository,
    ):
        self.orders = orders
        self.committed = False
        self.rolled_back = False

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True
