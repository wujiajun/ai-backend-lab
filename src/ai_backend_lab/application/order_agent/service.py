from collections.abc import AsyncIterator

from ai_backend_lab.application.exceptions import (
    LLMOutputError,
)
from ai_backend_lab.application.order_agent.exceptions import AgentMaxStepsExceededError
from ai_backend_lab.application.order_agent.executor import (
    ToolExecutor,
)
from ai_backend_lab.application.order_agent.models import (
    AgentAnswerEvent,
    AgentApprovalRequiredEvent,
    AgentApprovalResult,
    AgentCompletedEvent,
    AgentEvent,
    AgentResult,
    AgentRunResult,
    AgentStartedEvent,
    AgentState,
    AgentStep,
    AgentToolCalledEvent,
    AgentToolCompletedEvent,
    ConversationState,
)
from ai_backend_lab.application.order_agent.prompts import ORDER_AGENT_INSTRUCTIONS
from ai_backend_lab.application.order_agent.registry import (
    ToolRegistry,
)
from ai_backend_lab.application.ports.llm import (
    LLMGateway,
    LLMMessage,
    LLMRequest,
    LLMRole,
    LLMToolOutput,
)


class OrderAgentService:
    def __init__(
        self,
        llm: LLMGateway,
        registry: ToolRegistry,
        executor: ToolExecutor,
        max_steps: int,
    ) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1.")
        self._llm = llm
        self._registry = registry
        self._executor = executor
        self._max_steps = max_steps

    async def run(
        self,
        user_message: str,
        conversation: ConversationState | None = None,
    ) -> AgentRunResult:
        if conversation is None:
            conversation = ConversationState()
        state = AgentState(
            user_message=user_message,
            conversation=conversation,
        )

        return await self._continue(
            state,
            pending_tool_outputs=[],
        )

    async def resume(
        self,
        state: AgentState,
        approved_call_ids: set[str],
        rejected_call_ids: set[str],
    ) -> AgentRunResult:
        if not state.pending_tool_calls:
            raise ValueError("Agent state has no pending tool calls.")

        approval_requests = self._executor.required_approvals(
            state.pending_tool_calls,
            approved_call_ids,
            rejected_call_ids,
        )

        if approval_requests:
            return AgentApprovalResult(state=state, requests=approval_requests)

        tool_outputs = await self._executor.execute_resolved(
            tool_calls=state.pending_tool_calls,
            approved_call_ids=approved_call_ids,
            rejected_call_ids=rejected_call_ids,
        )
        step = AgentStep(
            number=len(state.steps) + 1,
            tool_calls=state.pending_tool_calls,
        )
        step.tool_outputs.extend(tool_outputs)

        state.steps.append(step)

        state.pending_tool_calls = []
        return await self._continue(state, pending_tool_outputs=tool_outputs)

    async def stream(
        self,
        user_message: str,
        conversation: ConversationState | None = None,
    ) -> AsyncIterator[AgentEvent]:
        if conversation is None:
            conversation = ConversationState()

        state = AgentState(
            user_message=user_message,
            conversation=conversation,
        )

        yield AgentStartedEvent()

        async for event in self._continue_stream(
            state=state,
            pending_tool_outputs=[],
        ):
            yield event

    async def _continue_stream(
        self,
        state: AgentState,
        pending_tool_outputs: list[LLMToolOutput],
    ) -> AsyncIterator[AgentEvent]:
        while True:
            request = self._build_request(
                state=state,
                tool_outputs=pending_tool_outputs,
            )

            result = await self._llm.generate(request)
            state.continuation_id = result.continuation_id

            if not result.tool_calls:
                state.conversation.messages.extend(
                    [
                        LLMMessage(
                            role=LLMRole.USER,
                            content=state.user_message,
                        ),
                        LLMMessage(
                            role=LLMRole.ASSISTANT,
                            content=result.text,
                        ),
                    ]
                )
                agent_result = AgentResult(
                    answer=result.text,
                    steps=len(state.steps),
                    conversation=state.conversation,
                )
                yield AgentAnswerEvent(
                    answer=result.text,
                )

                yield AgentCompletedEvent(
                    result=agent_result,
                )
                return

            if len(state.steps) >= self._max_steps:
                raise AgentMaxStepsExceededError(
                    "Agent exceeded the maximum "
                    f"number of tool steps: "
                    f"{self._max_steps}."
                )

            if result.continuation_id is None:
                raise LLMOutputError("LLM tool call response " "cannot be continued.")

            for tool_call in result.tool_calls:
                yield AgentToolCalledEvent(
                    call_id=tool_call.call_id,
                    tool_name=tool_call.name,
                    arguments=tool_call.arguments,
                )

            approval_requests = self._executor.required_approvals(
                result.tool_calls,
                approved_call_ids=set(),
                rejected_call_ids=set(),
            )

            if approval_requests:
                state.pending_tool_calls = result.tool_calls
                yield AgentApprovalRequiredEvent(
                    requests=approval_requests,
                )
                return

            tool_outputs = await self._executor.execute_all(result.tool_calls)
            for output in tool_outputs:
                yield AgentToolCompletedEvent(
                    call_id=output.call_id, output=output.output
                )

            step = AgentStep(
                number=len(state.steps) + 1,
                tool_calls=result.tool_calls,
            )

            step.tool_outputs.extend(tool_outputs)
            state.steps.append(step)
            pending_tool_outputs = tool_outputs

    def _build_request(
        self,
        state: AgentState,
        tool_outputs: list[LLMToolOutput],
    ) -> LLMRequest:
        if state.continuation_id is None:
            return LLMRequest(
                instructions=ORDER_AGENT_INSTRUCTIONS,
                messages=[
                    *state.conversation.messages,
                    LLMMessage(
                        role=LLMRole.USER,
                        content=state.user_message,
                    ),
                ],
                tools=self._registry.definitions(),
            )
        return LLMRequest(
            instructions=ORDER_AGENT_INSTRUCTIONS,
            continuation_id=state.continuation_id,
            tool_outputs=tool_outputs,
            tools=self._registry.definitions(),
        )

    async def _continue(
        self,
        state: AgentState,
        pending_tool_outputs: list[LLMToolOutput],
    ) -> AgentRunResult:
        while True:
            request = self._build_request(
                state,
                pending_tool_outputs,
            )

            result = await self._llm.generate(request)
            state.continuation_id = result.continuation_id

            # No tool call means the model has finished.
            if not result.tool_calls:
                state.conversation.messages.extend(
                    [
                        LLMMessage(role=LLMRole.USER, content=state.user_message),
                        LLMMessage(role=LLMRole.ASSISTANT, content=result.text),
                    ]
                )
                return AgentResult(
                    answer=result.text,
                    steps=len(state.steps),
                    conversation=state.conversation,
                )

            # The model wants another tool step,
            # but the execution budget has been exhausted.
            if len(state.steps) >= self._max_steps:
                raise AgentMaxStepsExceededError(
                    "Agent exceeded the maximum "
                    f"number of tool steps: {self._max_steps}."
                )

            # Tool outputs must be sent back to the
            # same LLM interaction.
            if result.continuation_id is None:
                raise LLMOutputError("LLM tool call response cannot be continued.")

            approval_requests = self._executor.required_approvals(
                result.tool_calls,
                approved_call_ids=set(),
                rejected_call_ids=set(),
            )

            # Do not execute any tool in this batch
            # until all required approvals are granted.
            if approval_requests:
                state.pending_tool_calls = result.tool_calls
                return AgentApprovalResult(
                    state=state,
                    requests=approval_requests,
                )

            tool_outputs = await self._executor.execute_all(result.tool_calls)

            step = AgentStep(
                number=len(state.steps) + 1,
                tool_calls=result.tool_calls,
            )
            step.tool_outputs.extend(tool_outputs)
            state.steps.append(step)

            pending_tool_outputs = tool_outputs
