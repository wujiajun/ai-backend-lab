import asyncio

from ai_backend_lab.application.ports.order_commands import (
    CancelOrderCommand,
    CancelOrderResult,
    OrderCommandGateway,
    OrderCommandNotFoundError,
    OrderCommandRejectedError,
)
from ai_backend_lab.application.services import (
    OrderService,
)
from ai_backend_lab.domain.exceptions import (
    OrderCannotBeCancelledError,
    OrderNotFoundError,
)


class LocalOrderCommandGateway(OrderCommandGateway):
    def __init__(
        self,
        order_service: OrderService,
    ) -> None:
        self._order_service = order_service

    async def cancel_order(
        self,
        command: CancelOrderCommand,
    ) -> CancelOrderResult:
        try:
            order = await asyncio.to_thread(
                self._order_service.cancel_order,
                command.order_number,
            )

        except OrderNotFoundError as exc:
            raise OrderCommandNotFoundError(str(exc)) from exc

        except OrderCannotBeCancelledError as exc:
            raise OrderCommandRejectedError(str(exc)) from exc

        return CancelOrderResult(
            order_number=order.order_number,
            status=order.status.value,
        )
