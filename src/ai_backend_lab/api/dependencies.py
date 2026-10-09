from typing import Annotated

import httpx
from fastapi import Depends, Request
from openai import AsyncOpenAI

from ai_backend_lab.application.order_assistant.service import OrderAssistantService
from ai_backend_lab.application.ports.llm import (
    LLMGateway,
)
from ai_backend_lab.application.ports.risk import RiskGateway
from ai_backend_lab.application.services import OrderService
from ai_backend_lab.composition import (
    build_order_assistant_service,
    build_order_service,
)
from ai_backend_lab.config import load_settings
from ai_backend_lab.infrastructure.database.database import session_factory
from ai_backend_lab.infrastructure.llm.gateway import (
    OpenAILLMGateway,
)
from ai_backend_lab.infrastructure.risk import HttpRiskGateway


def get_risk_gateway(request: Request) -> RiskGateway:
    settings = load_settings()

    client: httpx.AsyncClient = request.app.state.http_client

    return HttpRiskGateway(
        client=client,
        max_attempts=settings.risk_max_attempts,
        retry_initial_wait=(settings.risk_retry_initial_wait),
        retry_max_wait=settings.risk_retry_max_wait,
    )


RiskGatewayDep = Annotated[RiskGateway, Depends(get_risk_gateway)]


def get_order_service(
    risk_gateway: RiskGatewayDep,
) -> OrderService:
    return build_order_service(
        session_factory=session_factory, risk_gateway=risk_gateway
    )


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]


def get_llm_gateway(request: Request) -> LLMGateway:
    settings = load_settings()

    client: AsyncOpenAI = request.app.state.openai_client

    return OpenAILLMGateway(
        client=client,
        model=settings.llm_model,
        max_output_tokens=settings.llm_max_output_tokens,
        max_attempts=settings.llm_max_attempts,
        retry_initial_wait=settings.llm_retry_initial_wait,
        retry_max_wait=settings.llm_retry_max_wait,
    )


LLMGatewayDep = Annotated[LLMGateway, Depends(get_llm_gateway)]


def get_order_assistant_service(
    llm_gateway: LLMGatewayDep, risk_gateway: RiskGatewayDep
) -> OrderAssistantService:
    return build_order_assistant_service(
        session_factory=session_factory,
        llm_gateway=llm_gateway,
        risk_gateway=risk_gateway,
    )


OrderAssistantServiceDep = Annotated[
    OrderAssistantService, Depends(get_order_assistant_service)
]
