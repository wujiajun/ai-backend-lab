from sqlalchemy.orm import Session, sessionmaker

from ai_backend_lab.application.order_assistant.service import OrderAssistantService
from ai_backend_lab.application.ports.llm import LLMGateway
from ai_backend_lab.application.ports.risk import RiskGateway
from ai_backend_lab.application.services import OrderService
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
