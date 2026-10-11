import asyncio

from ai_backend_lab.application.exceptions import (
    LLMOutputError,
)
from ai_backend_lab.application.order_agent.models import AgentApprovalRequest
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
        if self._all_parallel_safe(tool_calls):
            return await self._execute_parallel(tool_calls)

        return await self._execute_sequential(tool_calls)

    def _all_parallel_safe(
        self,
        tool_calls: list[LLMToolCall],
    ) -> bool:
        if len(tool_calls) < 2:
            return False

        for tool_call in tool_calls:
            tool = self._registry.get(tool_call.name)

            if tool is None:
                return False

            if not tool.policy.parallel_safe:
                return False

        return True

    async def _execute_sequential(
        self,
        tool_calls: list[LLMToolCall],
    ) -> list[LLMToolOutput]:
        outputs: list[LLMToolOutput] = []

        for tool_call in tool_calls:
            output = await self.execute(tool_call)

            outputs.append(output)

        return outputs

    async def _execute_parallel(
        self,
        tool_calls: list[LLMToolCall],
    ) -> list[LLMToolOutput]:
        tasks: list[asyncio.Task[LLMToolOutput]] = []

        async with asyncio.TaskGroup() as group:
            for tool_call in tool_calls:
                task = group.create_task(self.execute(tool_call))

                tasks.append(task)

        return [task.result() for task in tasks]

    def required_approvals(
        self,
        tool_calls: list[LLMToolCall],
        approved_call_ids: set[str],
    ) -> list[AgentApprovalRequest]:
        requests: list[AgentApprovalRequest] = []

        for tool_call in tool_calls:
            tool = self._registry.get(tool_call.name)

            if tool is None:
                raise LLMOutputError(f"Unsupported tool: {tool_call.name}")

            if (
                tool.policy.requires_approval
                and tool_call.call_id not in approved_call_ids
            ):
                requests.append(
                    AgentApprovalRequest(
                        call_id=tool_call.call_id,
                        tool_name=tool_call.name,
                        arguments=tool_call.arguments,
                    )
                )

        return requests
