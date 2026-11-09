import grpc
import pytest

from ai_backend_lab.application.ports.order_commands import (
    CancelOrderCommand,
    OrderCommandIntegrationError,
    OrderCommandNotFoundError,
    OrderCommandRejectedError,
    OrderCommandTimeoutError,
    OrderCommandUnavailableError,
)
from ai_backend_lab.contracts.order.v1 import order_service_pb2
from ai_backend_lab.infrastructure.order_commands.grpc import (
    GrpcOrderCommandGateway,
)


class FakeOrderCommandStub:
    def __init__(
        self,
        *,
        response: order_service_pb2.CancelOrderResponse | None = None,
        error: grpc.aio.AioRpcError | None = None,
    ) -> None:
        self._response = response
        self._error = error

        self.requests: list[order_service_pb2.CancelOrderRequest] = []
        self.timeouts: list[float] = []

    async def CancelOrder(
        self,
        request: order_service_pb2.CancelOrderRequest,
        timeout: float,
    ) -> order_service_pb2.CancelOrderResponse:
        self.requests.append(request)
        self.timeouts.append(timeout)

        if self._error is not None:
            raise self._error

        assert self._response is not None
        return self._response


def _rpc_error(code: grpc.StatusCode) -> grpc.aio.AioRpcError:
    return grpc.aio.AioRpcError(
        code=code,
        initial_metadata=grpc.aio.Metadata(),
        trailing_metadata=grpc.aio.Metadata(),
        details="boom",
    )


COMMAND = CancelOrderCommand(
    order_number="ORD-001",
    idempotency_key="run-001:call-001",
)


@pytest.mark.asyncio
async def test_cancel_order_sends_idempotency_key_and_deadline() -> None:
    stub = FakeOrderCommandStub(
        response=order_service_pb2.CancelOrderResponse(
            order_number="ORD-001",
            status=order_service_pb2.ORDER_STATUS_CANCELLED,
        )
    )
    gateway = GrpcOrderCommandGateway(stub=stub, timeout_seconds=2.0)

    result = await gateway.cancel_order(COMMAND)

    assert result.order_number == "ORD-001"
    assert result.status == "Cancelled"
    assert stub.requests[0].order_number == "ORD-001"
    assert stub.requests[0].idempotency_key == "run-001:call-001"
    assert stub.timeouts == [2.0]


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        (grpc.StatusCode.NOT_FOUND, OrderCommandNotFoundError),
        (grpc.StatusCode.FAILED_PRECONDITION, OrderCommandRejectedError),
        (grpc.StatusCode.DEADLINE_EXCEEDED, OrderCommandTimeoutError),
        (grpc.StatusCode.UNAVAILABLE, OrderCommandUnavailableError),
        (grpc.StatusCode.INTERNAL, OrderCommandIntegrationError),
    ],
)
@pytest.mark.asyncio
async def test_cancel_order_maps_grpc_errors(
    code: grpc.StatusCode,
    expected: type[Exception],
) -> None:
    stub = FakeOrderCommandStub(error=_rpc_error(code))
    gateway = GrpcOrderCommandGateway(stub=stub, timeout_seconds=2.0)

    with pytest.raises(expected) as exc_info:
        await gateway.cancel_order(COMMAND)

    assert type(exc_info.value) is expected


@pytest.mark.asyncio
async def test_cancel_order_rejects_unspecified_status() -> None:
    stub = FakeOrderCommandStub(
        response=order_service_pb2.CancelOrderResponse(
            order_number="ORD-001",
            status=order_service_pb2.ORDER_STATUS_UNSPECIFIED,
        )
    )
    gateway = GrpcOrderCommandGateway(stub=stub, timeout_seconds=2.0)

    with pytest.raises(OrderCommandIntegrationError):
        await gateway.cancel_order(COMMAND)
