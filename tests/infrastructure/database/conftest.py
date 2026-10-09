from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, delete
from sqlalchemy.orm import Session

from ai_backend_lab.infrastructure.database.models import OrderRecord


@pytest.fixture
def db_session(test_engine: Engine) -> Iterator[Session]:
    connection = test_engine.connect()
    transaction = connection.begin()

    session = Session(bind=connection, expire_on_commit=False)

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def clean_uow_test_data(uow_session_factory) -> Iterator[None]:
    try:
        yield
    finally:
        with uow_session_factory() as session:
            session.execute(
                delete(OrderRecord).where(OrderRecord.order_number.like("UOWTEST%"))
            )
            session.commit()
