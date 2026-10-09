import asyncio
from collections.abc import AsyncIterator

from pydantic import ValidationError

from ai_backend_lab.application.exceptions import (
    LLMOutputError,
)
from ai_backend_lab.application.order_assistant.models import (
    OrderIntent,
)
from ai_backend_lab.application.order_assistant.prompts import (
    ORDER_INTENT_INSTRUCTIONS,
    ORDER_QUESTION_INSTRUCTIONS,
    ORDER_TOOL_INSTRUCTIONS,
)
from ai_backend_lab.application.order_assistant.tools import (
    GET_ORDER_TOOL,
    GetOrderArguments,
    GetOrderToolOutput,
)
from ai_backend_lab.application.ports.llm import (
    LLMGateway,
    LLMMessage,
    LLMRequest,
    LLMRole,
    LLMToolCall,
    LLMToolOutput,
)
from ai_backend_lab.application.services import OrderService


class OrderAssistantService:
    def __init__(
        self,
        llm: LLMGateway,
        order_service: OrderService,
    ) -> None:
        self._llm = llm
        self._order_service = order_service

    async def extract_intent(
        self,
        user_message: str,
    ) -> OrderIntent:
        result = await self._llm.generate_structured(
            LLMRequest(
                instructions=ORDER_INTENT_INSTRUCTIONS,
                messages=[
                    LLMMessage(
                        role=LLMRole.USER,
                        content=user_message,
                    )
                ],
            ),
            OrderIntent,
        )

        return result.value

    async def stream_answer(
        self,
        user_message: str,
    ) -> AsyncIterator[str]:
        request = LLMRequest(
            instructions=ORDER_QUESTION_INSTRUCTIONS,
            messages=[
                LLMMessage(
                    role=LLMRole.USER,
                    content=user_message,
                )
            ],
        )

        async for chunk in self._llm.stream(request):
            yield chunk

    async def answer_with_tools(
        self,
        user_message: str,
    ) -> str:
        first_result = await self._llm.generate(
            LLMRequest(
                instructions=ORDER_TOOL_INSTRUCTIONS,
                messages=[
                    LLMMessage(
                        role=LLMRole.USER,
                        content=user_message,
                    )
                ],
                tools=[
                    GET_ORDER_TOOL,
                ],
            )
        )

        if not first_result.tool_calls:
            return first_result.text

        if first_result.continuation_id is None:
            raise LLMOutputError("LLM response cannot be continued.")

        tool_outputs = [
            await self._execute_tool_call(tool_call)
            for tool_call in first_result.tool_calls
        ]

        final_result = await self._llm.generate(
            LLMRequest(
                instructions=ORDER_TOOL_INSTRUCTIONS,
                continuation_id=(first_result.continuation_id),
                tool_outputs=tool_outputs,
            )
        )

        return final_result.text

    async def _execute_tool_call(
        self,
        tool_call: LLMToolCall,
    ) -> LLMToolOutput:
        if tool_call.name != GET_ORDER_TOOL.name:
            raise LLMOutputError(f"Unsupported tool: {tool_call.name}")

        try:
            arguments = GetOrderArguments.model_validate_json(tool_call.arguments)
        except ValidationError as exc:
            raise LLMOutputError("LLM returned invalid tool arguments.") from exc

        order = await asyncio.to_thread(
            self._order_service.get_order,
            arguments.order_number,
        )

        result = GetOrderToolOutput(
            found=order is not None,
            order_number=(
                order.order_number if order is not None else arguments.order_number
            ),
            status=order.status if order is not None else None,
            amount=order.amount if order is not None else None,
        )

        return LLMToolOutput(
            call_id=tool_call.call_id,
            output=result.model_dump_json(),
        )
