import logging
from collections.abc import AsyncIterator
from time import perf_counter

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
    AgentStepTrace,
    AgentToolCalledEvent,
    AgentToolCompletedEvent,
    ConversationState,
)
from ai_backend_lab.application.order_agent.prompts import ORDER_AGENT_INSTRUCTIONS
from ai_backend_lab.application.order_agent.registry import (
    ToolRegistry,
)
from ai_backend_lab.application.order_agent.tool_execution import (
    ToolExecutionContext,
)
from ai_backend_lab.application.ports.llm import (
    LLMGateway,
    LLMMessage,
    LLMRequest,
    LLMResult,
    LLMRole,
    LLMToolCall,
    LLMToolOutput,
)

logger = logging.getLogger(__name__)


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
        run_id: str,
        user_message: str,
        conversation: ConversationState | None = None,
    ) -> AgentRunResult:
        if conversation is None:
            conversation = ConversationState()
        state = AgentState(
            run_id=run_id,
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

        if state.pending_llm_duration_ms is None:
            raise ValueError("Agent state has no pending LLM duration.")

        tool_calls = state.pending_tool_calls

        tool_started = perf_counter()

        tool_outputs = await self._executor.execute_resolved(
            tool_calls=tool_calls,
            rejected_call_ids=rejected_call_ids,
            context=ToolExecutionContext(
                run_id=state.run_id,
            ),
        )

        tool_duration_ms = (perf_counter() - tool_started) * 1000

        self._record_completed_tool_step(
            state=state,
            tool_calls=tool_calls,
            tool_outputs=tool_outputs,
            llm_duration_ms=(state.pending_llm_duration_ms),
            tool_duration_ms=tool_duration_ms,
        )

        state.pending_tool_calls = []
        state.pending_llm_duration_ms = None
        return await self._continue(state, pending_tool_outputs=tool_outputs)

    async def stream(
        self,
        run_id: str,
        user_message: str,
        conversation: ConversationState | None = None,
    ) -> AsyncIterator[AgentEvent]:
        if conversation is None:
            conversation = ConversationState()

        state = AgentState(
            run_id=run_id,
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

            result, llm_duration_ms = await self._generate_with_trace(
                state=state,
                request=request,
            )
            state.continuation_id = result.continuation_id

            if not result.tool_calls:
                agent_result = self._complete(
                    state=state,
                    answer=result.text,
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
                state.pending_llm_duration_ms = llm_duration_ms
                yield AgentApprovalRequiredEvent(
                    requests=approval_requests,
                )
                return

            tool_started = perf_counter()

            tool_outputs = await self._executor.execute_all(
                result.tool_calls,
                ToolExecutionContext(state.run_id),
            )

            tool_duration_ms = (perf_counter() - tool_started) * 1000

            for output in tool_outputs:
                yield AgentToolCompletedEvent(
                    call_id=output.call_id, output=output.output
                )

            self._record_completed_tool_step(
                state=state,
                tool_calls=result.tool_calls,
                tool_outputs=tool_outputs,
                llm_duration_ms=llm_duration_ms,
                tool_duration_ms=tool_duration_ms,
            )

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
            result, llm_duration_ms = await self._generate_with_trace(
                state=state,
                request=request,
            )
            state.continuation_id = result.continuation_id

            # No tool call means the model has finished.
            if not result.tool_calls:
                return self._complete(
                    state=state,
                    answer=result.text,
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
                state.pending_llm_duration_ms = llm_duration_ms
                return AgentApprovalResult(
                    state=state,
                    requests=approval_requests,
                )

            tool_started = perf_counter()
            tool_outputs = await self._executor.execute_all(
                result.tool_calls,
                ToolExecutionContext(state.run_id),
            )
            tool_duration_ms = (perf_counter() - tool_started) * 1000

            self._record_completed_tool_step(
                state=state,
                tool_calls=result.tool_calls,
                tool_outputs=tool_outputs,
                llm_duration_ms=llm_duration_ms,
                tool_duration_ms=tool_duration_ms,
            )

            pending_tool_outputs = tool_outputs

    def _record_llm_usage(
        self,
        state: AgentState,
        result: LLMResult,
    ) -> None:
        state.trace.llm_calls += 1

        if result.usage is None:
            return

        state.trace.input_tokens += result.usage.input_tokens
        state.trace.output_tokens += result.usage.output_tokens

    def _record_completed_tool_step(
        self,
        state: AgentState,
        tool_calls: list[LLMToolCall],
        tool_outputs: list[LLMToolOutput],
        llm_duration_ms: float,
        tool_duration_ms: float,
    ) -> None:
        step_number = len(state.steps) + 1

        step = AgentStep(
            number=step_number,
            tool_calls=tool_calls,
        )

        step.tool_outputs.extend(tool_outputs)

        state.steps.append(step)

        state.trace.tool_calls += len(tool_calls)

        state.trace.steps.append(
            AgentStepTrace(
                step_number=step_number,
                llm_duration_ms=llm_duration_ms,
                tool_names=[tool_call.name for tool_call in tool_calls],
                tool_duration_ms=tool_duration_ms,
            )
        )

    def _complete(
        self,
        state: AgentState,
        answer: str,
    ) -> AgentResult:
        state.conversation.messages.extend(
            [
                LLMMessage(
                    role=LLMRole.USER,
                    content=state.user_message,
                ),
                LLMMessage(
                    role=LLMRole.ASSISTANT,
                    content=answer,
                ),
            ]
        )

        result = AgentResult(
            answer=answer,
            steps=len(state.steps),
            conversation=state.conversation,
            trace=state.trace,
        )

        logger.info(
            "Agent completed "
            "steps=%s "
            "llm_calls=%s "
            "tool_calls=%s "
            "input_tokens=%s "
            "output_tokens=%s",
            result.steps,
            state.trace.llm_calls,
            state.trace.tool_calls,
            state.trace.input_tokens,
            state.trace.output_tokens,
        )

        return result

    async def _generate_with_trace(
        self,
        state: AgentState,
        request: LLMRequest,
    ) -> tuple[LLMResult, float]:
        started = perf_counter()

        result = await self._llm.generate(request)

        duration_ms = (perf_counter() - started) * 1000

        self._record_llm_usage(
            state=state,
            result=result,
        )

        return result, duration_ms
