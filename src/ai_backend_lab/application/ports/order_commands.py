from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CancelOrderCommand:
    order_number: str
    idempotency_key: str


@dataclass(frozen=True)
class CancelOrderResult:
    order_number: str
    status: str


class OrderCommandGateway(Protocol):
    async def cancel_order(
        self,
        command: CancelOrderCommand,
    ) -> CancelOrderResult: ...


class OrderCommandError(Exception):
    pass


class OrderCommandNotFoundError(OrderCommandError):
    pass


class OrderCommandRejectedError(OrderCommandError):
    pass


class OrderCommandIntegrationError(OrderCommandError):
    pass


class OrderCommandUnavailableError(OrderCommandIntegrationError):
    pass


class OrderCommandTimeoutError(OrderCommandIntegrationError):
    pass
