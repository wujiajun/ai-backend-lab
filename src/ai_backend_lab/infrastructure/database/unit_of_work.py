from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session, sessionmaker

from ai_backend_lab.application.ports.repositories import OrderRepository
from ai_backend_lab.infrastructure.database.repositories import (
    SqlAlchemyOrderRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory
        self._session: Session | None = None
        self.orders: OrderRepository

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        self.orders = SqlAlchemyOrderRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ):
        if self._session is None:
            return
        try:
            if exc_type is not None:
                self.rollback()
        finally:
            self._session.close()

    def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork is not active.")

        self._session.commit()

    def rollback(self) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork is not active.")

        self._session.rollback()
