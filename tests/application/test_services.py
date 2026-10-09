import json
from decimal import Decimal

import pytest

from ai_backend_lab.application.exceptions import (
    LLMOutputError,
)
from ai_backend_lab.application.order_assistant.models import (
    OrderAction,
    OrderIntent,
)
from ai_backend_lab.application.order_assistant.service import (
    OrderAssistantService,
)
from ai_backend_lab.application.ports.llm import LLMResult, LLMToolCall
from ai_backend_lab.application.queries import OrderQuery
from ai_backend_lab.application.services import OrderService
from ai_backend_lab.domain.exceptions import (
    DuplicateOrderError,
    OrderCannotBeCancelledError,
    OrderNotFoundError,
    OrderRejectedError,
)
from ai_backend_lab.domain.models import Order, OrderStatus
from ai_backend_lab.infrastructure.risk import RiskAssessment
from tests.fakes.llm import FakeLLMGateway
from tests.fakes.order_numbers import FakeOrderNumberGenerator
from tests.fakes.risk import FakeRiskGateway
from tests.fakes.unit_of_work import FakeUnitOfWork


def test_get_order_returns_existing_order(
    order_service: OrderService,
) -> None:
    order = order_service.get_order("A001")

    assert order is not None
    assert order.id == 1
    assert order.order_number == "A001"
    assert order.customer_name == "Alice"


def test_get_order_raises_when_not_found(
    order_service: OrderService,
) -> None:
    with pytest.raises(OrderNotFoundError):
        order_service.get_order_or_raise("UNKNOWN")


@pytest.mark.asyncio
async def test_create_order_saves_and_commits(
    order_service: OrderService,
    uow: FakeUnitOfWork,
) -> None:
    order = await order_service.create_order(
        customer_name="David",
        amount=Decimal("99.00"),
    )

    assert order.order_number == "TEST-ORDER-001"
    assert order.id is not None
    assert order.status == OrderStatus.PENDING
    assert uow.committed is True

    saved = uow.orders.find_by_order_number("TEST-ORDER-001")
    assert saved is not None


def test_cancel_order_saves_and_commits(
    order_service: OrderService,
    uow: FakeUnitOfWork,
) -> None:
    order = order_service.cancel_order("A002")

    assert order.status == OrderStatus.CANCELLED
    assert uow.committed is True


def test_cancel_shipped_order_does_not_commit(
    order_service: OrderService,
    uow: FakeUnitOfWork,
) -> None:
    with pytest.raises(OrderCannotBeCancelledError):
        order_service.cancel_order("A003")

    assert uow.committed is False
    assert uow.rolled_back is True


def test_find_orders_filters_by_customer(
    order_service: OrderService,
) -> None:
    orders = order_service.find_orders(OrderQuery(customer_name="Bob"))

    assert len(orders) == 1
    assert orders[0].id == 2
    assert orders[0].order_number == "A002"


@pytest.mark.asyncio
async def test_create_duplicate_order_raises_error(uow: FakeUnitOfWork) -> None:
    generator = FakeOrderNumberGenerator("A001")
    risk_gateway = FakeRiskGateway()
    service = OrderService(
        uow=uow, order_number_generator=generator, risk_gateway=risk_gateway
    )
    with pytest.raises(DuplicateOrderError):
        await service.create_order(
            customer_name="Another Alice",
            amount=Decimal("999.00"),
        )
    assert uow.committed is False
    assert uow.rolled_back is True


@pytest.mark.asyncio
async def test_create_order_does_not_persist_when_risk_rejects(
    uow: FakeUnitOfWork,
    order_number_generator: FakeOrderNumberGenerator,
) -> None:
    risk_gateway = FakeRiskGateway(
        RiskAssessment(
            approved=False,
            reason="Risk rejected.",
        )
    )

    service = OrderService(
        uow=uow,
        order_number_generator=order_number_generator,
        risk_gateway=risk_gateway,
    )

    with pytest.raises(OrderRejectedError):
        await service.create_order(
            customer_name="Alice",
            amount=Decimal("9999.00"),
        )

    assert uow.committed is False


@pytest.mark.asyncio
async def test_extract_intent(order_service: OrderService) -> None:
    llm = FakeLLMGateway(
        structured_values=[
            OrderIntent(
                action=OrderAction.CANCEL,
                order_number="ORD-001",
            )
        ],
    )
    service = OrderAssistantService(llm=llm, order_service=order_service)  # type: ignore

    result = await service.extract_intent("Cancel ORD-001.")

    assert result.action == OrderAction.CANCEL
    assert result.order_number == "ORD-001"


@pytest.mark.asyncio
async def test_stream_answer(
    order_service: OrderService,
) -> None:
    llm = FakeLLMGateway(
        stream_chunks=[
            "Your ",
            "order ",
            "is pending.",
        ]
    )

    service = OrderAssistantService(
        llm=llm,
        order_service=order_service,
    )

    chunks = [
        chunk async for chunk in service.stream_answer("What is my order status?")
    ]

    assert chunks == [
        "Your ",
        "order ",
        "is pending.",
    ]


@pytest.mark.asyncio
async def test_answer_with_tools_gets_order(
    order_service: OrderService,
    uow: FakeUnitOfWork,
) -> None:
    uow.orders.add(
        Order(
            id=None,
            order_number="ORD-001",
            customer_name="Alice",
            amount=Decimal("120.00"),
            status=OrderStatus.PENDING,
        )
    )
    llm = FakeLLMGateway(
        results=[
            LLMResult(
                text="",
                tool_calls=[
                    LLMToolCall(
                        call_id="call-001",
                        name="get_order",
                        arguments='{"order_number": "ORD-001"}',
                    )
                ],
                continuation_id="response-001",
            ),
            LLMResult(
                text="Order ORD-001 is pending.",
            ),
        ],
    )

    service = OrderAssistantService(
        llm=llm,
        order_service=order_service,
    )

    answer = await service.answer_with_tools("What is the status of order ORD-001?")

    assert answer == "Order ORD-001 is pending."

    assert len(llm.requests) == 2

    first_request = llm.requests[0]
    assert first_request.tool_outputs == []

    second_request = llm.requests[1]
    assert second_request.continuation_id == "response-001"
    assert len(second_request.tool_outputs) == 1

    tool_output = second_request.tool_outputs[0]

    assert tool_output.call_id == "call-001"

    output = json.loads(tool_output.output)

    assert output["found"] is True
    assert output["order_number"] == "ORD-001"
    assert output["status"] == "Pending"
    assert output["amount"] == "120.00"


@pytest.mark.asyncio
async def test_answer_with_tools_returns_not_found_output(
    order_service: OrderService,
) -> None:
    llm = FakeLLMGateway(
        results=[
            LLMResult(
                text="",
                tool_calls=[
                    LLMToolCall(
                        call_id="call-001",
                        name="get_order",
                        arguments=('{"order_number":"WRONG"}'),
                    )
                ],
                continuation_id="response-001",
            ),
            LLMResult(
                text=("I couldn't find that order."),
            ),
        ]
    )

    service = OrderAssistantService(
        llm=llm,
        order_service=order_service,
    )

    answer = await service.answer_with_tools("What is the status of WRONG?")

    assert answer == ("I couldn't find that order.")

    output = json.loads(llm.requests[1].tool_outputs[0].output)

    assert output["found"] is False
    assert output["order_number"] == "WRONG"


@pytest.mark.asyncio
async def test_answer_with_tools_rejects_invalid_arguments(
    order_service: OrderService,
) -> None:
    llm = FakeLLMGateway(
        results=[
            LLMResult(
                text="",
                tool_calls=[
                    LLMToolCall(
                        call_id="call-001",
                        name="get_order",
                        arguments='{"foo":"bar"}',
                    )
                ],
                continuation_id="response-001",
            )
        ]
    )

    service = OrderAssistantService(
        llm=llm,
        order_service=order_service,
    )

    with pytest.raises(LLMOutputError):
        await service.answer_with_tools("Find my order.")


@pytest.mark.asyncio
async def test_answer_with_tools_returns_direct_answer(
    order_service: OrderService,
) -> None:
    llm = FakeLLMGateway(
        results=[
            LLMResult(
                text="Hello! How can I help you?",
            )
        ]
    )

    service = OrderAssistantService(
        llm=llm,
        order_service=order_service,
    )

    answer = await service.answer_with_tools("Hello!")

    assert answer == "Hello! How can I help you?"

    assert len(llm.requests) == 1


@pytest.mark.asyncio
async def test_answer_with_tools_rejects_unsupported_tool(
    order_service: OrderService,
) -> None:
    llm = FakeLLMGateway(
        results=[
            LLMResult(
                text="",
                tool_calls=[
                    LLMToolCall(
                        call_id="call-001",
                        name="delete_everything",
                        arguments="{}",
                    )
                ],
                continuation_id="response-001",
            )
        ]
    )

    service = OrderAssistantService(
        llm=llm,
        order_service=order_service,
    )

    with pytest.raises(
        LLMOutputError,
        match="Unsupported tool",
    ):
        await service.answer_with_tools("Delete everything.")

    assert len(llm.requests) == 1
