from decimal import Decimal

import pytest

from ai_backend_lab.domain.exceptions import (
    OrderCannotBeCancelledError,
)
from ai_backend_lab.domain.models import Order, OrderStatus


def test_pending_order_can_be_cancelled() -> None:
    order = Order(
        id=1,
        order_number="A001",
        customer_name="Alice",
        amount=Decimal("120.00"),
        status=OrderStatus.PENDING,
    )

    order.cancel()

    assert order.status == OrderStatus.CANCELLED


def test_shipped_order_cannot_be_cancelled() -> None:
    order = Order(
        id=1,
        order_number="A001",
        customer_name="Alice",
        amount=Decimal("120.00"),
        status=OrderStatus.SHIPPED,
    )

    with pytest.raises(OrderCannotBeCancelledError):
        order.cancel()


def test_shipped_order_is_not_cancellable() -> None:
    order = Order(
        id=1,
        order_number="A001",
        customer_name="Alice",
        amount=Decimal("120.00"),
        status=OrderStatus.SHIPPED,
    )

    assert order.can_be_cancelled is False


def test_create_pending_order() -> None:
    order = Order.create_pending(
        order_number="A001",
        customer_name="Alice",
        amount=Decimal("120.00"),
    )

    assert order.id is None
    assert order.order_number == "A001"
    assert order.customer_name == "Alice"
    assert order.amount == Decimal("120.00")
    assert order.status == OrderStatus.PENDING
