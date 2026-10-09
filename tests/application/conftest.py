from decimal import Decimal

import pytest

from ai_backend_lab.application.services import OrderService
from ai_backend_lab.domain.models import Order, OrderStatus
from tests.fakes.order_numbers import FakeOrderNumberGenerator
from tests.fakes.repositories import InMemoryOrderRepository
from tests.fakes.risk import FakeRiskGateway
from tests.fakes.unit_of_work import FakeUnitOfWork


@pytest.fixture
def order_repository() -> InMemoryOrderRepository:
    return InMemoryOrderRepository(
        [
            Order(
                id=1,
                order_number="A001",
                customer_name="Alice",
                amount=Decimal("120.00"),
                status=OrderStatus.PAID,
            ),
            Order(
                id=2,
                order_number="A002",
                customer_name="Bob",
                amount=Decimal("45.50"),
                status=OrderStatus.PENDING,
            ),
            Order(
                id=3,
                order_number="A003",
                customer_name="Charlie",
                amount=Decimal("300.00"),
                status=OrderStatus.SHIPPED,
            ),
        ]
    )


@pytest.fixture
def uow(
    order_repository: InMemoryOrderRepository,
) -> FakeUnitOfWork:
    return FakeUnitOfWork(order_repository)


@pytest.fixture
def order_number_generator() -> FakeOrderNumberGenerator:
    return FakeOrderNumberGenerator("TEST-ORDER-001")


@pytest.fixture
def risk_gateway() -> FakeRiskGateway:
    return FakeRiskGateway()


@pytest.fixture
def order_service(
    uow: FakeUnitOfWork,
    order_number_generator: FakeOrderNumberGenerator,
    risk_gateway: FakeRiskGateway,
) -> OrderService:
    return OrderService(uow, order_number_generator, risk_gateway)
