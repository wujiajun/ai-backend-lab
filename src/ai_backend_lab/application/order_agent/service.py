from ai_backend_lab.application.exceptions import (
    LLMOutputError,
)
from ai_backend_lab.application.order_agent.exceptions import AgentMaxStepsExceededError
from ai_backend_lab.application.order_agent.executor import (
    ToolExecutor,
)
from ai_backend_lab.application.order_agent.models import (
    AgentResult,
    AgentState,
    AgentStep,
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
    ) -> AgentResult:
        state = AgentState(
            user_message=user_message,
        )
        pending_tool_outputs: list[LLMToolOutput] = []

        while True:
            request = self._build_request(
                state,
                pending_tool_outputs,
            )

            result = await self._llm.generate(request)
            state.continuation_id = result.continuation_id

            if not result.tool_calls:
                return AgentResult(
                    answer=result.text,
                    steps=len(state.steps),
                )
            if len(state.steps) >= self._max_steps:
                raise AgentMaxStepsExceededError(
                    "Agent exceeded the maximum "
                    f"number of tool steps: {self._max_steps}."
                )

            if result.continuation_id is None:
                raise LLMOutputError("LLM tool call response cannot be continued.")

            tool_outputs = await self._executor.execute_all(result.tool_calls)

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
                    LLMMessage(
                        role=LLMRole.USER,
                        content=state.user_message,
                    )
                ],
                tools=self._registry.definitions(),
            )
        return LLMRequest(
            instructions=ORDER_AGENT_INSTRUCTIONS,
            continuation_id=state.continuation_id,
            tool_outputs=tool_outputs,
            tools=self._registry.definitions(),
        )
