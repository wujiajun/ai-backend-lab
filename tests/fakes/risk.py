from decimal import Decimal

from ai_backend_lab.application.ports.risk import (
    RiskAssessment,
)


class FakeRiskGateway:
    def __init__(
        self,
        assessment: RiskAssessment | None = None,
    ):
        self._assessment = assessment or RiskAssessment(
            approved=True,
        )

    async def assess(
        self,
        customer_name: str,
        amount: Decimal,
    ) -> RiskAssessment:
        return self._assessment
