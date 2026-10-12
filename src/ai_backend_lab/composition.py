from sqlalchemy.orm import Session, sessionmaker

from ai_backend_lab.application.order_agent.executor import (
    ToolExecutor,
)
from ai_backend_lab.application.order_agent.registry import (
    ToolRegistry,
)
from ai_backend_lab.application.order_agent.run_service import (
    AgentRunService,
)
from ai_backend_lab.application.order_agent.service import (
    OrderAgentService,
)
from ai_backend_lab.application.order_agent.tools import (
    CancelOrderTool,
    GetOrderTool,
)
from ai_backend_lab.application.order_assistant.service import OrderAssistantService
from ai_backend_lab.application.ports.llm import LLMGateway
from ai_backend_lab.application.ports.risk import RiskGateway
from ai_backend_lab.application.services import OrderService
from ai_backend_lab.infrastructure.agent.run_store import (
    SqlAlchemyAgentRunStore,
)
from ai_backend_lab.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from ai_backend_lab.infrastructure.order_number import UuidOrderNumberGenerator


def build_order_service(
    session_factory: sessionmaker[Session],
    risk_gateway: RiskGateway,
) -> OrderService:
    uow = SqlAlchemyUnitOfWork(session_factory)
    order_number_generator = UuidOrderNumberGenerator()
    return OrderService(uow, order_number_generator, risk_gateway)


def build_order_assistant_service(
    session_factory: sessionmaker[Session],
    llm_gateway: LLMGateway,
    risk_gateway: RiskGateway,
) -> OrderAssistantService:
    order_service = build_order_service(session_factory, risk_gateway)
    return OrderAssistantService(llm_gateway, order_service)


def build_order_agent_service(
    session_factory: sessionmaker[Session],
    llm: LLMGateway,
    risk_gateway: RiskGateway,
    max_steps: int,
) -> OrderAgentService:
    order_service = build_order_service(
        session_factory=session_factory,
        risk_gateway=risk_gateway,
    )

    get_order_tool = GetOrderTool(
        order_service=order_service,
    )

    cancel_order_tool = CancelOrderTool(
        order_service=order_service,
    )

    registry = ToolRegistry(
        tools=[
            get_order_tool,
            cancel_order_tool,
        ]
    )

    executor = ToolExecutor(
        registry=registry,
    )

    return OrderAgentService(
        llm=llm,
        registry=registry,
        executor=executor,
        max_steps=max_steps,
    )


def build_agent_run_service(
    session_factory: sessionmaker[Session],
    llm: LLMGateway,
    risk_gateway: RiskGateway,
    max_steps: int,
) -> AgentRunService:
    agent = build_order_agent_service(
        session_factory=session_factory,
        llm=llm,
        risk_gateway=risk_gateway,
        max_steps=max_steps,
    )

    store = SqlAlchemyAgentRunStore(
        session_factory=session_factory,
    )

    return AgentRunService(
        agent=agent,
        store=store,
    )
