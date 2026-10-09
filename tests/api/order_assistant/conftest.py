from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from ai_backend_lab.api.app import app
from ai_backend_lab.api.dependencies import get_llm_gateway, get_risk_gateway
from ai_backend_lab.application.ports.llm import LLMGateway, LLMResult
from ai_backend_lab.application.ports.risk import RiskGateway
from tests.fakes.llm import FakeLLMGateway
from tests.fakes.risk import FakeRiskGateway


@pytest.fixture
def assistant_client() -> Iterator[TestClient]:
    fake_llm = FakeLLMGateway(
        results=[
            LLMResult(
                text="Hello! How can I help?",
            )
        ]
    )
    fake_risk_gateway = FakeRiskGateway()

    def override_get_llm_gateway() -> LLMGateway:
        return fake_llm

    def override_get_risk_gateway() -> RiskGateway:
        return fake_risk_gateway

    app.dependency_overrides[get_llm_gateway] = override_get_llm_gateway
    app.dependency_overrides[get_risk_gateway] = override_get_risk_gateway
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
