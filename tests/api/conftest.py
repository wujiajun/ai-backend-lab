from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session, sessionmaker

from ai_backend_lab.api.app import app
from ai_backend_lab.api.dependencies import get_order_service
from ai_backend_lab.application.services import OrderService
from ai_backend_lab.infrastructure.database.models import OrderRecord
from ai_backend_lab.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from tests.fakes.order_numbers import FakeOrderNumberGenerator
from tests.fakes.risk import FakeRiskGateway


@pytest.fixture
def client(uow_session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    def override_get_order_service() -> OrderService:
        uow = SqlAlchemyUnitOfWork(uow_session_factory)
        generator = FakeOrderNumberGenerator("APITEST-001")
        risk_gateway = FakeRiskGateway()
        return OrderService(
            uow=uow,
            order_number_generator=generator,
            risk_gateway=risk_gateway,
        )

    app.dependency_overrides[get_order_service] = override_get_order_service

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def clean_api_test_data(uow_session_factory: sessionmaker[Session]) -> Iterator[None]:
    def cleanup() -> None:
        with uow_session_factory() as session:
            session.execute(
                delete(OrderRecord).where(OrderRecord.order_number.like("APITEST%"))
            )
            session.commit()

    cleanup()
    try:
        yield
    finally:
        cleanup()
