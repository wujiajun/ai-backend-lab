import os
from typing import Iterator

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

# @pytest.fixture
# def order_service() -> OrderService:
#     return OrderService(
#         InMemoryOrderRepository(
#             [
#                 Order("A001", "Alice", Decimal("120.00"), OrderStatus.PAID),
#                 Order("A002", "Bob", Decimal("45.50"), OrderStatus.PENDING),
#                 Order("A003", "Charlie", Decimal("300.00"), OrderStatus.SHIPPED),
#                 Order("A004", "Bob", Decimal("20.00"), OrderStatus.CANCELLED),
#                 Order("A005", "Eve", Decimal("180.00"), OrderStatus.PENDING),
#             ]
#         )
#     )


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    database_url = os.environ["TEST_DATABASE_URL"]

    url = make_url(database_url)

    if url.database != "ai_backend_lab_test":
        raise RuntimeError("Integration tests must use ai_backend_lab_test.")

    engine = create_engine(database_url, pool_pre_ping=True)

    yield engine

    engine.dispose


@pytest.fixture
def uow_session_factory():
    database_url = os.environ["TEST_DATABASE_URL"]

    if not database_url.endswith("/ai_backend_lab_test"):
        raise RuntimeError("Integration tests must use ai_backend_lab_test.")

    engine = create_engine(database_url, pool_pre_ping=True)

    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    yield factory

    engine.dispose
