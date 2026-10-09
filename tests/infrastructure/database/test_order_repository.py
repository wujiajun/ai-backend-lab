from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from ai_backend_lab.application.queries import (
    OrderQuery,
    OrderSortField,
    SortDirection,
)
from ai_backend_lab.domain.exceptions import DuplicateOrderError
from ai_backend_lab.domain.models import Order, OrderStatus
from ai_backend_lab.infrastructure.database.repositories import (
    SqlAlchemyOrderRepository,
)


def test_add_and_find_order(db_session: Session) -> None:
    repository = SqlAlchemyOrderRepository(db_session)
    order = Order(
        id=None,
        order_number="TEST001",
        customer_name="Alice",
        amount=Decimal("120.00"),
        status=OrderStatus.PENDING,
    )

    repository.add(order)

    db_session.flush

    assert order.id is not None
    result = repository.find_by_id(order.id)

    assert result is not None
    assert result.id is not None
    assert result.order_number == "TEST001"
    assert result.customer_name == "Alice"
    assert result.amount == Decimal("120.00")
    assert result.status == OrderStatus.PENDING


def test_update_existing_order(db_session: Session) -> None:
    repository = SqlAlchemyOrderRepository(db_session)
    order = Order(
        id=None,
        order_number="TEST002",
        customer_name="Bob",
        amount=Decimal("45.50"),
        status=OrderStatus.PENDING,
    )

    repository.add(order)
    db_session.flush()

    order.status = OrderStatus.CANCELLED

    repository.update(order)
    db_session.flush()

    assert order.id is not None
    result = repository.find_by_id(order.id)

    assert result is not None
    assert result.id is not None
    assert result.order_number == "TEST002"
    assert result.status == OrderStatus.CANCELLED


def test_find_orders_with_filters(db_session: Session) -> None:
    repository = SqlAlchemyOrderRepository(db_session)

    orders = [
        Order(
            id=None,
            order_number="TEST101",
            customer_name="Alice",
            amount=Decimal("100.00"),
            status=OrderStatus.PENDING,
        ),
        Order(
            id=None,
            order_number="TEST102",
            customer_name="Alice",
            amount=Decimal("200.00"),
            status=OrderStatus.PAID,
        ),
        Order(
            id=None,
            order_number="TEST103",
            customer_name="Bob",
            amount=Decimal("300.00"),
            status=OrderStatus.PENDING,
        ),
        Order(
            id=None,
            order_number="TEST104",
            customer_name="Charlie",
            amount=Decimal("400.00"),
            status=OrderStatus.CANCELLED,
        ),
    ]

    for order in orders:
        repository.add(order)

    db_session.flush()

    alice_orders = repository.find(OrderQuery(customer_name="Alice"))

    assert len(alice_orders) == 2
    assert {order.order_number for order in alice_orders} == {
        "TEST101",
        "TEST102",
    }
    pending_orders = repository.find(OrderQuery(status=OrderStatus.PENDING))

    assert len(pending_orders) == 2
    assert {order.order_number for order in pending_orders} == {
        "TEST101",
        "TEST103",
    }

    alice_pending_orders = repository.find(
        OrderQuery(customer_name="Alice", status=OrderStatus.PENDING),
    )

    assert len(alice_pending_orders) == 1
    assert alice_pending_orders[0].order_number == "TEST101"


def test_add_duplicate_order_raises_error(
    db_session: Session,
) -> None:
    repository = SqlAlchemyOrderRepository(db_session)

    first = Order(
        id=None,
        order_number="TEST_DUPLICATE",
        customer_name="Alice",
        amount=Decimal("100.00"),
        status=OrderStatus.PENDING,
    )

    repository.add(first)

    duplicate = Order(
        id=None,
        order_number="TEST_DUPLICATE",
        customer_name="Bob",
        amount=Decimal("200.00"),
        status=OrderStatus.PENDING,
    )

    with pytest.raises(DuplicateOrderError):
        repository.add(duplicate)


def test_find_order_by_order_number(
    db_session: Session,
) -> None:
    repository = SqlAlchemyOrderRepository(db_session)

    order = Order(
        id=None,
        order_number="TEST002",
        customer_name="Bob",
        amount=Decimal("45.50"),
        status=OrderStatus.PENDING,
    )

    repository.add(order)

    result = repository.find_by_order_number("TEST002")

    assert result is not None
    assert result.order_number == "TEST002"
    assert result.id is not None


def test_find_orders_with_pagination(
    db_session: Session,
) -> None:
    repository = SqlAlchemyOrderRepository(db_session)

    for index in range(1, 5):
        repository.add(
            Order(
                id=None,
                order_number=f"PAGE{index:03d}",
                customer_name="PAGE_TEST",
                amount=Decimal(str(index * 10)),
                status=OrderStatus.PENDING,
            )
        )

    first_page = repository.find(
        OrderQuery(
            customer_name="PAGE_TEST",
            limit=2,
            offset=0,
            sort_by=OrderSortField.ID,
            sort_direction=SortDirection.DESC,
        )
    )

    second_page = repository.find(
        OrderQuery(
            customer_name="PAGE_TEST",
            limit=2,
            offset=2,
            sort_by=OrderSortField.ID,
            sort_direction=SortDirection.DESC,
        )
    )

    assert [order.order_number for order in first_page] == [
        "PAGE004",
        "PAGE003",
    ]

    assert [order.order_number for order in second_page] == [
        "PAGE002",
        "PAGE001",
    ]


def test_find_orders_sorted_by_amount(
    db_session: Session,
) -> None:
    repository = SqlAlchemyOrderRepository(db_session)

    test_orders = [
        Order(
            id=None,
            order_number="SORT001",
            customer_name="SORT_TEST",
            amount=Decimal("300.00"),
            status=OrderStatus.PENDING,
        ),
        Order(
            id=None,
            order_number="SORT002",
            customer_name="SORT_TEST",
            amount=Decimal("100.00"),
            status=OrderStatus.PENDING,
        ),
        Order(
            id=None,
            order_number="SORT003",
            customer_name="SORT_TEST",
            amount=Decimal("200.00"),
            status=OrderStatus.PENDING,
        ),
    ]

    for order in test_orders:
        repository.add(order)

    result = repository.find(
        OrderQuery(
            customer_name="SORT_TEST",
            sort_by=OrderSortField.AMOUNT,
            sort_direction=SortDirection.ASC,
        )
    )

    assert [order.order_number for order in result] == [
        "SORT002",
        "SORT003",
        "SORT001",
    ]


def test_find_orders_with_filter_sort_and_pagination(
    db_session: Session,
) -> None:
    repository = SqlAlchemyOrderRepository(db_session)

    test_orders = [
        Order(
            id=None,
            order_number="FILTER001",
            customer_name="FILTER_TEST",
            amount=Decimal("100.00"),
            status=OrderStatus.PENDING,
        ),
        Order(
            id=None,
            order_number="FILTER002",
            customer_name="FILTER_TEST",
            amount=Decimal("200.00"),
            status=OrderStatus.PAID,
        ),
        Order(
            id=None,
            order_number="FILTER003",
            customer_name="FILTER_TEST",
            amount=Decimal("300.00"),
            status=OrderStatus.PENDING,
        ),
    ]

    for order in test_orders:
        repository.add(order)

    result = repository.find(
        OrderQuery(
            customer_name="FILTER_TEST",
            status=OrderStatus.PENDING,
            limit=1,
            offset=0,
            sort_by=OrderSortField.AMOUNT,
            sort_direction=SortDirection.DESC,
        )
    )

    assert len(result) == 1
    assert result[0].order_number == "FILTER003"
