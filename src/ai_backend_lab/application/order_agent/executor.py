import asyncio
import json

from ai_backend_lab.application.exceptions import (
    LLMOutputError,
)
from ai_backend_lab.application.order_agent.exceptions import (
    ToolExecutionConflictError,
    ToolExecutionInProgressError,
    ToolExecutionIntentConflictError,
    ToolExecutionStateError,
    ToolExecutionUnknownOutcomeError,
)
from ai_backend_lab.application.order_agent.models import AgentApprovalRequest
from ai_backend_lab.application.order_agent.registry import (
    ToolRegistry,
)
from ai_backend_lab.application.order_agent.tool_execution import (
    ToolExecutionContext,
    ToolExecutionRecord,
    ToolExecutionStatus,
    ToolExecutionStore,
    build_tool_intent_hash,
)
from ai_backend_lab.application.ports.llm import (
    LLMToolCall,
    LLMToolOutput,
)


class ToolExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        execution_store: ToolExecutionStore,
    ) -> None:
        self._registry = registry
        self._execution_store = execution_store

    async def execute(
        self,
        tool_call: LLMToolCall,
        context: ToolExecutionContext,
    ) -> LLMToolOutput:
        tool = self._registry.get(tool_call.name)

        if tool is None:
            raise LLMOutputError(f"Unsupported tool: {tool_call.name}")

        intent_hash = build_tool_intent_hash(
            tool_name=tool_call.name,
            arguments=tool_call.arguments,
        )

        existing = await self._execution_store.get(
            run_id=context.run_id, call_id=tool_call.call_id
        )

        if existing is not None:
            return self._resolve_existing_execution(
                tool_call=tool_call,
                intent_hash=intent_hash,
                record=existing,
            )

        record = ToolExecutionRecord(
            run_id=context.run_id,
            call_id=tool_call.call_id,
            tool_name=tool_call.name,
            intent_hash=intent_hash,
            status=ToolExecutionStatus.STARTED,
        )
        try:
            await self._execution_store.create(record)
        except ToolExecutionConflictError:
            return await self._resolve_claim_conflict(
                tool_call=tool_call,
                context=context,
                intent_hash=intent_hash,
            )

        output = await tool.execute(tool_call.arguments)

        completed = await self._execution_store.complete(
            run_id=context.run_id,
            call_id=tool_call.call_id,
            output=output,
        )

        if completed.output is None:
            raise ToolExecutionStateError("Completed tool execution " "has no output.")

        return LLMToolOutput(
            call_id=tool_call.call_id,
            output=output,
        )

    async def _resolve_claim_conflict(
        self,
        tool_call: LLMToolCall,
        context: ToolExecutionContext,
        intent_hash: str,
    ) -> LLMToolOutput:
        existing = await self._execution_store.get(
            run_id=context.run_id,
            call_id=tool_call.call_id,
        )

        if existing is None:
            raise ToolExecutionStateError(
                "Tool execution claim conflicted, " "but no execution record exists."
            )

        return self._resolve_existing_execution(
            tool_call=tool_call,
            intent_hash=intent_hash,
            record=existing,
        )

    def _resolve_existing_execution(
        self,
        tool_call: LLMToolCall,
        intent_hash: str,
        record: ToolExecutionRecord,
    ) -> LLMToolOutput:
        if record.tool_name != tool_call.name or record.intent_hash != intent_hash:
            raise ToolExecutionIntentConflictError(
                "Tool execution key was reused " "with a different intent."
            )

        if record.status == ToolExecutionStatus.COMPLETED:
            if record.output is None:
                raise ToolExecutionStateError(
                    "Completed tool execution " "has no output."
                )

            return LLMToolOutput(
                call_id=tool_call.call_id,
                output=record.output,
            )

        if record.status == ToolExecutionStatus.STARTED:
            raise ToolExecutionInProgressError("Tool execution is already in progress.")

        if record.status == ToolExecutionStatus.UNKNOWN:
            raise ToolExecutionUnknownOutcomeError("Tool execution outcome is unknown.")

        raise ToolExecutionStateError(
            f"Unsupported tool execution status: " f"{record.status}."
        )

    async def execute_all(
        self,
        tool_calls: list[LLMToolCall],
        context: ToolExecutionContext,
    ) -> list[LLMToolOutput]:
        if self._all_parallel_safe(tool_calls):
            return await self._execute_parallel(
                tool_calls,
                context,
            )

        return await self._execute_sequential(
            tool_calls,
            context,
        )

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

    async def execute_resolved(
        self,
        tool_calls: list[LLMToolCall],
        rejected_call_ids: set[str],
        context: ToolExecutionContext,
    ) -> list[LLMToolOutput]:
        executable_calls: list[LLMToolCall] = []

        outputs_by_call_id: dict[
            str,
            LLMToolOutput,
        ] = {}

        for tool_call in tool_calls:
            if tool_call.call_id in rejected_call_ids:
                outputs_by_call_id[tool_call.call_id] = self._rejection_output(
                    tool_call
                )
            else:
                executable_calls.append(tool_call)

        executed_outputs = await self.execute_all(
            executable_calls,
            context,
        )

        for output in executed_outputs:
            outputs_by_call_id[output.call_id] = output

        return [outputs_by_call_id[tool_call.call_id] for tool_call in tool_calls]

    async def _execute_sequential(
        self,
        tool_calls: list[LLMToolCall],
        context: ToolExecutionContext,
    ) -> list[LLMToolOutput]:
        outputs: list[LLMToolOutput] = []

        for tool_call in tool_calls:
            output = await self.execute(
                tool_call,
                context,
            )

            outputs.append(output)

        return outputs

    async def _execute_parallel(
        self,
        tool_calls: list[LLMToolCall],
        context: ToolExecutionContext,
    ) -> list[LLMToolOutput]:
        tasks: list[asyncio.Task[LLMToolOutput]] = []

        async with asyncio.TaskGroup() as group:
            for tool_call in tool_calls:
                task = group.create_task(
                    self.execute(
                        tool_call,
                        context,
                    )
                )

                tasks.append(task)

        return [task.result() for task in tasks]

    def required_approvals(
        self,
        tool_calls: list[LLMToolCall],
        approved_call_ids: set[str],
        rejected_call_ids: set[str],
    ) -> list[AgentApprovalRequest]:
        requests: list[AgentApprovalRequest] = []

        for tool_call in tool_calls:
            tool = self._registry.get(tool_call.name)

            if tool is None:
                raise LLMOutputError(f"Unsupported tool: {tool_call.name}")

            if (
                tool.policy.requires_approval
                and tool_call.call_id not in approved_call_ids
                and tool_call.call_id not in rejected_call_ids
            ):
                requests.append(
                    AgentApprovalRequest(
                        call_id=tool_call.call_id,
                        tool_name=tool_call.name,
                        arguments=tool_call.arguments,
                    )
                )

        return requests

    def _rejection_output(
        self,
        tool_call: LLMToolCall,
    ) -> LLMToolOutput:
        return LLMToolOutput(
            call_id=tool_call.call_id,
            output=json.dumps(
                {
                    "ok": False,
                    "error_code": "USER_REJECTED",
                    "message": ("The user rejected this action."),
                }
            ),
        )
