import asyncio
from dataclasses import dataclass
from typing import Protocol

from pydantic import ValidationError

from ai_backend_lab.application.exceptions import (
    LLMOutputError,
)
from ai_backend_lab.application.order_assistant.tools import (
    CANCEL_ORDER_TOOL,
    GET_ORDER_TOOL,
    CancelOrderArguments,
    CancelOrderToolOutput,
    GetOrderArguments,
    GetOrderToolOutput,
)
from ai_backend_lab.application.ports.llm import (
    LLMToolDefinition,
)
from ai_backend_lab.application.services import (
    OrderService,
)


@dataclass(frozen=True)
class AgentToolPolicy:
    parallel_safe: bool = False
    requires_approval: bool = False


class AgentTool(Protocol):
    @property
    def definition(self) -> LLMToolDefinition: ...

    @property
    def policy(
        self,
    ) -> AgentToolPolicy: ...

    async def execute(
        self,
        arguments: str,
    ) -> str: ...


class GetOrderTool:
    def __init__(
        self,
        order_service: OrderService,
    ) -> None:
        self._order_service = order_service

    @property
    def definition(self) -> LLMToolDefinition:
        return GET_ORDER_TOOL

    @property
    def policy(
        self,
    ) -> AgentToolPolicy:
        return AgentToolPolicy(
            parallel_safe=False,
        )

    async def execute(
        self,
        arguments: str,
    ) -> str:
        try:
            args = GetOrderArguments.model_validate_json(arguments)
        except ValidationError as exc:
            raise LLMOutputError("LLM returned invalid get_order arguments.") from exc

        order = await asyncio.to_thread(
            self._order_service.get_order,
            args.order_number,
        )

        result = GetOrderToolOutput(
            found=order is not None,
            order_number=(
                order.order_number if order is not None else args.order_number
            ),
            status=(order.status if order is not None else None),
            amount=(order.amount if order is not None else None),
        )

        return result.model_dump_json()


class CancelOrderTool:
    def __init__(
        self,
        order_service: OrderService,
    ) -> None:
        self._order_service = order_service

    @property
    def definition(
        self,
    ) -> LLMToolDefinition:
        return CANCEL_ORDER_TOOL

    @property
    def policy(
        self,
    ) -> AgentToolPolicy:
        return AgentToolPolicy(
            parallel_safe=False,
            requires_approval=True,
        )

    async def execute(
        self,
        arguments: str,
    ) -> str:
        try:
            args = CancelOrderArguments.model_validate_json(arguments)
        except ValidationError as exc:
            raise LLMOutputError(
                "LLM returned invalid cancel_order arguments."
            ) from exc

        order = await asyncio.to_thread(
            self._order_service.cancel_order,
            args.order_number,
        )

        result = CancelOrderToolOutput(
            order_number=order.order_number,
            status=order.status,
        )

        return result.model_dump_json()
