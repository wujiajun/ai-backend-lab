from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ai_backend_lab.api.dependencies import OrderAssistantServiceDep
from ai_backend_lab.api.schemas.order_assistant import (
    AssistantRequest,
    OrderAssistantRequest,
    OrderAssistantResponse,
)

router = APIRouter(prefix="/order-assistant", tags=["order-assistant"])


@router.post("/stream")
async def stream_order_assistant(
    request: AssistantRequest,
    service: OrderAssistantServiceDep,
) -> StreamingResponse:
    return StreamingResponse(
        service.stream_answer(request.message),
        media_type="text/plain",
    )


@router.post(
    "/ask",
    response_model=OrderAssistantResponse,
)
async def ask_order_assistant(
    request: OrderAssistantRequest,
    service: OrderAssistantServiceDep,
) -> OrderAssistantResponse:
    answer = await service.answer_with_tools(request.message)

    return OrderAssistantResponse(answer=answer)
