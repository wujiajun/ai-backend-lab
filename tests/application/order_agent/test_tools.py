
from ai_backend_lab.application.order_agent.registry import ToolRegistry
from ai_backend_lab.application.order_agent.tools import GetOrderTool
from ai_backend_lab.application.services import OrderService


def test_registry_returns_registered_tool(
    order_service: OrderService,
) -> None:
    tool = GetOrderTool(order_service)

    registry = ToolRegistry([tool])

    result = registry.get("get_order")

    assert result is tool


def test_registry_returns_none_for_unknown_tool(
    order_service: OrderService,
) -> None:
    registry = ToolRegistry([GetOrderTool(order_service)])

    assert registry.get("unknown") is None
