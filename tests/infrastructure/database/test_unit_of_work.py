from decimal import Decimal

import pytest

from ai_backend_lab.domain.models import Order, OrderStatus
from ai_backend_lab.infrastructure.database.unit_of_work import (
    SqlAlchemyUnitOfWork,
)


def test_uow_commit_persists_order(
    uow_session_factory,
    clean_uow_test_data,
) -> None:
    uow = SqlAlchemyUnitOfWork(uow_session_factory)

    with uow:
        order = Order(
            id=None,
            order_number="UOWTEST001",
            customer_name="Alice",
            amount=Decimal("120.00"),
            status=OrderStatus.PENDING,
        )

        uow.orders.add(order)
        uow.commit()

    verify_uow = SqlAlchemyUnitOfWork(uow_session_factory)

    assert order.id is not None
    with verify_uow:
        result = verify_uow.orders.find_by_order_number("UOWTEST001")

    assert result is not None
    assert result.order_number == "UOWTEST001"
    assert result.customer_name == "Alice"
    assert result.amount == Decimal("120.00")
    assert result.status == OrderStatus.PENDING


def test_uow_rolls_back_on_exception(
    uow_session_factory,
    clean_uow_test_data,
) -> None:
    uow = SqlAlchemyUnitOfWork(uow_session_factory)

    with pytest.raises(RuntimeError):
        with uow:
            order = Order(
                id=None,
                order_number="UOWTEST002",
                customer_name="Bob",
                amount=Decimal("45.50"),
                status=OrderStatus.PENDING,
            )

            uow.orders.add(order)

            raise RuntimeError("Simulated failure")

    verify_uow = SqlAlchemyUnitOfWork(uow_session_factory)

    with verify_uow:
        result = verify_uow.orders.find_by_order_number("UOWTEST002")

    assert result is None
