from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from ai_backend_lab.api.errors import ErrorCode
from ai_backend_lab.domain.models import Order, OrderStatus
from ai_backend_lab.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def test_create_and_get_order(client: TestClient, clean_api_test_data: None) -> None:
    create_response = client.post(
        "/orders",
        json={
            "customer_name": "Alice",
            "amount": "120.00",
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()

    assert isinstance(created["id"], int)
    assert created["order_number"] == "APITEST-001"
    assert created["customer_name"] == "Alice"
    assert created["status"] == "Pending"

    get_response = client.get(f"/orders/{created["order_number"]}")

    assert get_response.status_code == 200

    fetched = get_response.json()

    assert fetched["order_number"] == "APITEST-001"
    assert fetched["customer_name"] == "Alice"
    assert fetched["status"] == "Pending"


def test_get_order_returns_404_when_not_found(
    client: TestClient, clean_api_test_data: None
) -> None:
    response = client.get("/orders/APITEST999")
    body = response.json()
    assert response.status_code == 404
    assert body["code"] == ErrorCode.ORDER_NOT_FOUND.value


def test_cancel_pending_order(client: TestClient, clean_api_test_data: None) -> None:
    create_response = client.post(
        "/orders",
        json={
            "customer_name": "Bob",
            "amount": "45.50",
        },
    )
    assert create_response.status_code == 201

    created = create_response.json()

    cancel_response = client.post(f"/orders/{created["order_number"]}/cancel")
    assert cancel_response.status_code == 200
    cancelled = cancel_response.json()
    assert cancelled["order_number"] == created["order_number"]
    assert cancelled["status"] == "Cancelled"

    get_response = client.get(f"/orders/{cancelled["order_number"]}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "Cancelled"


def test_cancel_shipped_order_returns_409(
    client: TestClient,
    uow_session_factory: sessionmaker[Session],
    clean_api_test_data: None,
) -> None:
    uow = SqlAlchemyUnitOfWork(uow_session_factory)

    with uow:
        order = Order(
            id=None,
            order_number="APITEST003",
            customer_name="Charlie",
            amount=Decimal("300.00"),
            status=OrderStatus.SHIPPED,
        )

        uow.orders.add(order)
        uow.commit()

    response = client.post("/orders/APITEST003/cancel")
    body = response.json()
    assert response.status_code == 409
    assert body["code"] == ErrorCode.ORDER_CANNOT_BE_CANCELLED.value


def test_create_order_returns_422_for_invalid_amount(
    client: TestClient,
) -> None:
    response = client.post(
        "/orders",
        json={
            "customer_name": "Alice",
            "amount": "-10.00",
        },
    )

    assert response.status_code == 422


def test_create_duplicate_order_returns_409(
    client: TestClient,
    clean_api_test_data: None,
) -> None:
    payload = {
        "customer_name": "Alice",
        "amount": "120.00",
    }

    first_response = client.post(
        "/orders",
        json=payload,
    )

    assert first_response.status_code == 201

    duplicate_response = client.post(
        "/orders",
        json=payload,
    )
    assert duplicate_response.status_code == 409

    body = duplicate_response.json()

    assert body["code"] == "DUPLICATE_ORDER"


def test_list_orders_with_pagination_and_sort(
    client: TestClient,
    uow_session_factory: sessionmaker[Session],
    clean_api_test_data: None,
) -> None:
    uow = SqlAlchemyUnitOfWork(uow_session_factory)

    with uow:
        orders = [
            Order(
                id=None,
                order_number="APITEST-PAGE-001",
                customer_name="Alice",
                amount=Decimal("300.00"),
                status=OrderStatus.PENDING,
            ),
            Order(
                id=None,
                order_number="APITEST-PAGE-002",
                customer_name="Alice",
                amount=Decimal("100.00"),
                status=OrderStatus.PENDING,
            ),
            Order(
                id=None,
                order_number="APITEST-PAGE-003",
                customer_name="Alice",
                amount=Decimal("200.00"),
                status=OrderStatus.PENDING,
            ),
        ]

        for order in orders:
            uow.orders.add(order)

        uow.commit()

    response = client.get(
        "/orders"
        "?customer_name=Alice"
        "&sort_by=amount"
        "&sort_direction=asc"
        "&limit=2"
        "&offset=0"
    )

    assert response.status_code == 200

    result = response.json()

    assert len(result) == 2

    assert [Decimal(order["amount"]) for order in result] == [
        Decimal("100.00"),
        Decimal("200.00"),
    ]


def test_list_orders_second_page(
    client: TestClient,
    uow_session_factory: sessionmaker[Session],
    clean_api_test_data: None,
) -> None:
    uow = SqlAlchemyUnitOfWork(uow_session_factory)

    with uow:
        orders = [
            Order(
                id=None,
                order_number="APITEST-PAGE-001",
                customer_name="Bob",
                amount=Decimal("10.00"),
                status=OrderStatus.PENDING,
            ),
            Order(
                id=None,
                order_number="APITEST-PAGE-002",
                customer_name="Bob",
                amount=Decimal("20.00"),
                status=OrderStatus.PENDING,
            ),
            Order(
                id=None,
                order_number="APITEST-PAGE-003",
                customer_name="Bob",
                amount=Decimal("30.00"),
                status=OrderStatus.PENDING,
            ),
        ]

        for order in orders:
            uow.orders.add(order)

        uow.commit()

    response = client.get(
        "/orders"
        "?customer_name=Bob"
        "&sort_by=amount"
        "&sort_direction=asc"
        "&limit=2"
        "&offset=2"
    )

    assert response.status_code == 200

    result = response.json()

    assert len(result) == 1
    assert Decimal(result[0]["amount"]) == Decimal("30.00")


def test_list_orders_returns_422_when_limit_is_too_large(
    client: TestClient,
) -> None:
    response = client.get("/orders?limit=101")

    assert response.status_code == 422

    body = response.json()

    assert body["code"] == ErrorCode.VALIDATION_ERROR.value


def test_list_orders_returns_422_for_invalid_sort_field(
    client: TestClient,
) -> None:
    response = client.get("/orders?sort_by=unknown")

    assert response.status_code == 422

    body = response.json()

    assert body["code"] == ErrorCode.VALIDATION_ERROR.value
