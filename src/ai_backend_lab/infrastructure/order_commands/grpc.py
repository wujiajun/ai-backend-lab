import grpc

from ai_backend_lab.application.ports.order_commands import (
    CancelOrderCommand,
    CancelOrderResult,
    OrderCommandGateway,
    OrderCommandIntegrationError,
    OrderCommandNotFoundError,
    OrderCommandRejectedError,
    OrderCommandTimeoutError,
    OrderCommandUnavailableError,
)
from ai_backend_lab.contracts.order.v1 import (
    order_service_pb2,
    order_service_pb2_grpc,
)

from typing import Never


class GrpcOrderCommandGateway(OrderCommandGateway):
    def __init__(
        self,
        stub: order_service_pb2_grpc.OrderCommandServiceStub,
        timeout_seconds: float,
    ) -> None:
        self._stub = stub
        self._timeout_seconds = timeout_seconds

    async def cancel_order(
        self,
        command: CancelOrderCommand,
    ) -> CancelOrderResult:
        request = order_service_pb2.CancelOrderRequest(
            order_number=(command.order_number),
            idempotency_key=(command.idempotency_key),
        )

        try:
            response = await self._stub.CancelOrder(
                request,
                timeout=self._timeout_seconds,
            )

        except grpc.aio.AioRpcError as exc:
            self._raise_mapped_error(exc)

        return CancelOrderResult(
            order_number=response.order_number,
            status=self._map_status(response.status),
        )

    @staticmethod
    def _raise_mapped_error(
        exc: grpc.aio.AioRpcError,
    ) -> Never:
        code = exc.code()
        details = exc.details() or "Order service RPC failed."

        if code == grpc.StatusCode.NOT_FOUND:
            raise OrderCommandNotFoundError(details) from exc

        if code == grpc.StatusCode.FAILED_PRECONDITION:
            raise OrderCommandRejectedError(details) from exc

        if code == grpc.StatusCode.DEADLINE_EXCEEDED:
            raise OrderCommandTimeoutError(details) from exc

        if code == grpc.StatusCode.UNAVAILABLE:
            raise OrderCommandUnavailableError(details) from exc

        raise OrderCommandIntegrationError(
            f"Order service RPC failed: " f"{code.name}: {details}"
        ) from exc

    @staticmethod
    def _map_status(
        status: int,
    ) -> str:
        mapping = {
            int(order_service_pb2.ORDER_STATUS_PENDING): "Pending",
            int(order_service_pb2.ORDER_STATUS_PAID): "Paid",
            int(order_service_pb2.ORDER_STATUS_SHIPPED): "Shipped",
            int(order_service_pb2.ORDER_STATUS_CANCELLED): "Cancelled",
        }

        result = mapping.get(int(status))

        if result is None:
            raise OrderCommandIntegrationError(
                "Order service returned " "an unsupported order status."
            )

        return result
