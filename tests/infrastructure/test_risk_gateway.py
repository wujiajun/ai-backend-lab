from decimal import Decimal

import httpx
import pytest

from ai_backend_lab.application.exceptions import (
    RiskServiceIntegrationError,
    RiskServiceUnavailableError,
)
from ai_backend_lab.infrastructure.risk import (
    HttpRiskGateway,
)


@pytest.mark.asyncio
async def test_risk_gateway_returns_approved_assessment() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "approved": True,
                "reason": None,
            },
            request=request,
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://risk.test",
    ) as client:
        gateway = HttpRiskGateway(
            client=client,
            max_attempts=3,
            retry_initial_wait=0.0,
            retry_max_wait=0.0,
        )

        result = await gateway.assess(
            customer_name="Alice",
            amount=Decimal("120.00"),
        )

    assert result.approved is True
    assert result.reason is None


@pytest.mark.asyncio
async def test_risk_gateway_sends_expected_request() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/assess"

        return httpx.Response(
            200,
            json={
                "approved": True,
            },
            request=request,
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://risk.test",
    ) as client:
        gateway = HttpRiskGateway(
            client=client,
            max_attempts=1,
            retry_initial_wait=0.0,
            retry_max_wait=0.0,
        )

        await gateway.assess(
            customer_name="Alice",
            amount=Decimal("120.00"),
        )


@pytest.mark.asyncio
async def test_risk_gateway_retries_and_then_succeeds() -> None:
    attempts = 0

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        nonlocal attempts

        attempts += 1

        if attempts < 3:
            return httpx.Response(
                503,
                request=request,
            )

        return httpx.Response(
            200,
            json={
                "approved": True,
            },
            request=request,
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://risk.test",
    ) as client:
        gateway = HttpRiskGateway(
            client=client,
            max_attempts=3,
            retry_initial_wait=0.0,
            retry_max_wait=0.0,
        )

        result = await gateway.assess(
            customer_name="Alice",
            amount=Decimal("120.00"),
        )

    assert attempts == 3
    assert result.approved is True


@pytest.mark.asyncio
async def test_risk_gateway_raises_unavailable_after_timeouts() -> None:
    attempts = 0

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        nonlocal attempts

        attempts += 1

        raise httpx.ReadTimeout(
            "Risk service timed out.",
            request=request,
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://risk.test",
    ) as client:
        gateway = HttpRiskGateway(
            client=client,
            max_attempts=3,
            retry_initial_wait=0.0,
            retry_max_wait=0.0,
        )

        with pytest.raises(RiskServiceUnavailableError):
            await gateway.assess(
                customer_name="Alice",
                amount=Decimal("120.00"),
            )

    assert attempts == 3


@pytest.mark.asyncio
async def test_risk_gateway_does_not_retry_401() -> None:
    attempts = 0

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        nonlocal attempts

        attempts += 1

        return httpx.Response(
            401,
            request=request,
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://risk.test",
    ) as client:
        gateway = HttpRiskGateway(
            client=client,
            max_attempts=3,
            retry_initial_wait=0.0,
            retry_max_wait=0.0,
        )

        with pytest.raises(RiskServiceIntegrationError):
            await gateway.assess(
                customer_name="Alice",
                amount=Decimal("120.00"),
            )

    assert attempts == 1


@pytest.mark.asyncio
async def test_risk_gateway_rejects_invalid_json() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"not-json",
            request=request,
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://risk.test",
    ) as client:
        gateway = HttpRiskGateway(
            client=client,
            max_attempts=1,
            retry_initial_wait=0.0,
            retry_max_wait=0.0,
        )

        with pytest.raises(RiskServiceIntegrationError):
            await gateway.assess(
                customer_name="Alice",
                amount=Decimal("120.00"),
            )


@pytest.mark.asyncio
async def test_risk_gateway_rejects_invalid_schema() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "decision": "ALLOW",
            },
            request=request,
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://risk.test",
    ) as client:
        gateway = HttpRiskGateway(
            client=client,
            max_attempts=1,
            retry_initial_wait=0.0,
            retry_max_wait=0.0,
        )

        with pytest.raises(RiskServiceIntegrationError):
            await gateway.assess(
                customer_name="Alice",
                amount=Decimal("120.00"),
            )
