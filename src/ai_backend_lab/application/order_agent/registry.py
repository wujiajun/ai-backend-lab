from collections.abc import Iterable

from ai_backend_lab.application.order_agent.tools import (
    AgentTool,
)
from ai_backend_lab.application.ports.llm import (
    LLMToolDefinition,
)


class ToolRegistry:
    def __init__(
        self,
        tools: Iterable[AgentTool],
    ) -> None:
        self._tools: dict[str, AgentTool] = {}

        for tool in tools:
            name = tool.definition.name

            if name in self._tools:
                raise ValueError(f"Duplicate tool name: {name}")

            self._tools[name] = tool

    def get(
        self,
        name: str,
    ) -> AgentTool | None:
        return self._tools.get(name)

    def definitions(
        self,
    ) -> list[LLMToolDefinition]:
        return [tool.definition for tool in self._tools.values()]
