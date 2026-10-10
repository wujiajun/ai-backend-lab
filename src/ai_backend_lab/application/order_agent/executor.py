from ai_backend_lab.application.exceptions import (
    LLMOutputError,
)
from ai_backend_lab.application.order_agent.registry import (
    ToolRegistry,
)
from ai_backend_lab.application.ports.llm import (
    LLMToolCall,
    LLMToolOutput,
)


class ToolExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
    ) -> None:
        self._registry = registry

    async def execute(
        self,
        tool_call: LLMToolCall,
    ) -> LLMToolOutput:
        tool = self._registry.get(tool_call.name)

        if tool is None:
            raise LLMOutputError(f"Unsupported tool: {tool_call.name}")

        output = await tool.execute(tool_call.arguments)

        return LLMToolOutput(
            call_id=tool_call.call_id,
            output=output,
        )

    async def execute_all(
        self,
        tool_calls: list[LLMToolCall],
    ) -> list[LLMToolOutput]:
        outputs: list[LLMToolOutput] = []

        for tool_call in tool_calls:
            output = await self.execute(tool_call)

            outputs.append(output)

        return outputs
