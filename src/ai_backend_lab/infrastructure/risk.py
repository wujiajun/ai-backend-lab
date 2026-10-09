from decimal import Decimal
from json import JSONDecodeError

import httpx
from pydantic import BaseModel, ValidationError
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from ai_backend_lab.application.exceptions import (
    RiskServiceIntegrationError,
    RiskServiceUnavailableError,
)
from ai_backend_lab.application.ports.risk import (
    RiskAssessment,
)

RETRYABLE_STATUS_CODES = {
    429,
    502,
    503,
    504,
}


class _RetryableRiskError(Exception):
    pass


class RiskResponse(BaseModel):
    approved: bool
    reason: str | None = None


class HttpRiskGateway:
    def __init__(
        self,
        client: httpx.AsyncClient,
        max_attempts: int,
        retry_initial_wait: float,
        retry_max_wait: float,
    ) -> None:
        self._client = client
        self._max_attempts = max_attempts
        self._retry_initial_wait = retry_initial_wait
        self._retry_max_wait = retry_max_wait

    async def assess(
        self,
        customer_name: str,
        amount: Decimal,
    ) -> RiskAssessment:
        try:
            async for attemp in AsyncRetrying(
                stop=stop_after_attempt(self._max_attempts),
                wait=wait_exponential_jitter(
                    initial=self._retry_initial_wait, max=self._retry_max_wait
                ),
                retry=retry_if_exception_type(_RetryableRiskError),
                reraise=True,
            ):
                with attemp:
                    response = await self._request_assessment(
                        customer_name=customer_name,
                        amount=amount,
                    )
        except _RetryableRiskError as exc:
            raise RiskServiceUnavailableError(
                "Risk service is temporarily unavailable."
            ) from exc

        return self._parse_response(response)

    async def _request_assessment(
        self,
        customer_name: str,
        amount: Decimal,
    ) -> httpx.Response:
        try:
            response = await self._client.post(
                "/assess",
                json={
                    "customer_name": customer_name,
                    "amount": str(amount),
                },
            )

        except (
            httpx.TimeoutException,
            httpx.ConnectError,
        ) as exc:
            raise _RetryableRiskError("Risk service request failed.") from exc

        if response.status_code in RETRYABLE_STATUS_CODES:
            raise _RetryableRiskError(
                f"Risk service returned " f"{response.status_code}."
            )

        if response.is_error:
            raise RiskServiceIntegrationError(
                "Risk service returned an "
                f"unexpected status: {response.status_code}."
            )

        return response

    def _parse_response(
        self,
        response: httpx.Response,
    ) -> RiskAssessment:
        try:
            payload = response.json()

            data = RiskResponse.model_validate(payload)

        except (
            JSONDecodeError,
            ValidationError,
        ) as exc:
            raise RiskServiceIntegrationError(
                "Risk service returned an invalid response."
            ) from exc

        return RiskAssessment(
            approved=data.approved,
            reason=data.reason,
        )
