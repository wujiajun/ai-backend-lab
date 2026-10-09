from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class RiskAssessment:
    approved: bool
    reason: str | None = None


class RiskGateway(Protocol):
    async def assess(
        self,
        customer_name: str,
        amount: Decimal,
    ) -> RiskAssessment: ...
