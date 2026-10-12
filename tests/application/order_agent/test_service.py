import json

import pytest

from ai_backend_lab.application.order_agent.exceptions import (
    AgentMaxStepsExceededError,
)
from ai_backend_lab.application.order_agent.executor import (
    ToolExecutor,
)
from ai_backend_lab.application.order_agent.models import (
    AgentApprovalResult,
    AgentResult,
)
from ai_backend_lab.application.order_agent.registry import (
    ToolRegistry,
)
from ai_backend_lab.application.order_agent.service import (
    OrderAgentService,
)
from ai_backend_lab.application.order_agent.tools import (
    AgentToolPolicy,
)
from ai_backend_lab.application.ports.llm import (
    LLMResult,
    LLMToolCall,
    LLMToolDefinition,
    LLMUsage,
)
from tests.fakes.llm import FakeLLMGateway


class FakeAgentTool:
    def __init__(
        self,
        *,
        name: str,
        output: str,
        requires_approval: bool = False,
    ) -> None:
        self._definition = LLMToolDefinition(
            name=name,
            description=f"Fake tool: {name}",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        )

        self._output = output
        self._requires_approval = requires_approval

        self.executed_arguments: list[str] = []

    @property
    def definition(
        self,
    ) -> LLMToolDefinition:
        return self._definition

    @property
    def policy(
        self,
    ) -> AgentToolPolicy:
        return AgentToolPolicy(
            parallel_safe=False,
            requires_approval=self._requires_approval,
        )

    async def execute(
        self,
        arguments: str,
    ) -> str:
        self.executed_arguments.append(arguments)

        return self._output


@pytest.mark.asyncio
async def test_agent_returns_direct_answer() -> None:
    llm = FakeLLMGateway(
        results=[
            LLMResult(
                text="Hello! How can I help?",
                usage=LLMUsage(
                    input_tokens=10,
                    output_tokens=5,
                ),
            )
        ]
    )

    registry = ToolRegistry(tools=[])

    executor = ToolExecutor(registry=registry)

    agent = OrderAgentService(
        llm=llm,
        registry=registry,
        executor=executor,
        max_steps=6,
    )

    result = await agent.run("Hello!")

    assert isinstance(
        result,
        AgentResult,
    )

    assert result.answer == ("Hello! How can I help?")

    assert result.steps == 0

    assert result.trace.llm_calls == 1
    assert result.trace.tool_calls == 0

    assert result.trace.input_tokens == 10
    assert result.trace.output_tokens == 5

    assert len(result.conversation.messages) == 2

    assert result.conversation.messages[0].content == "Hello!"

    assert result.conversation.messages[1].content == "Hello! How can I help?"


@pytest.mark.asyncio
async def test_agent_executes_tool_and_returns_final_answer() -> None:
    tool = FakeAgentTool(
        name="get_order",
        output=('{"found":true,' '"order_number":"ORD-001",' '"status":"Pending"}'),
    )

    registry = ToolRegistry(
        tools=[
            tool,
        ]
    )

    executor = ToolExecutor(
        registry=registry,
    )
    llm = FakeLLMGateway(
        results=[
            LLMResult(
                text="",
                tool_calls=[
                    LLMToolCall(
                        call_id="call-001",
                        name="get_order",
                        arguments=('{"order_number":"ORD-001"}'),
                    )
                ],
                continuation_id="response-001",
            ),
            LLMResult(
                text="ORD-001 is pending.",
            ),
        ]
    )
    agent = OrderAgentService(
        llm=llm,
        registry=registry,
        executor=executor,
        max_steps=6,
    )
    result = await agent.run("What is the status of ORD-001?")

    assert isinstance(
        result,
        AgentResult,
    )

    assert result.answer == ("ORD-001 is pending.")

    assert result.steps == 1

    assert tool.executed_arguments == ['{"order_number":"ORD-001"}']

    assert len(llm.requests) == 2

    second_request = llm.requests[1]

    assert second_request.continuation_id == "response-001"

    assert len(second_request.tool_outputs) == 1

    tool_output = second_request.tool_outputs[0]

    assert tool_output.call_id == "call-001"

    output = json.loads(tool_output.output)

    assert output["found"] is True
    assert output["status"] == "Pending"

    assert result.trace.llm_calls == 2
    assert result.trace.tool_calls == 1

    assert len(result.trace.steps) == 1

    assert result.trace.steps[0].tool_names == ["get_order"]


@pytest.mark.asyncio
async def test_agent_runs_multiple_tool_steps() -> None:
    tool = FakeAgentTool(
        name="get_order",
        output=('{"found":true,' '"order_number":"ORD-001",' '"status":"Pending"}'),
    )
    registry = ToolRegistry(
        tools=[
            tool,
        ]
    )

    executor = ToolExecutor(
        registry=registry,
    )
    llm = FakeLLMGateway(
        results=[
            LLMResult(
                text="",
                tool_calls=[
                    LLMToolCall(
                        call_id="call-001",
                        name="get_order",
                        arguments=('{"order_number":"ORD-001"}'),
                    )
                ],
                continuation_id="response-001",
            ),
            LLMResult(
                text="",
                tool_calls=[
                    LLMToolCall(
                        call_id="call-002",
                        name="get_order",
                        arguments=('{"order_number":"ORD-002"}'),
                    )
                ],
                continuation_id="response-002",
            ),
            LLMResult(
                text=("I checked both orders."),
            ),
        ]
    )
    agent = OrderAgentService(
        llm=llm,
        registry=registry,
        executor=executor,
        max_steps=6,
    )
    result = await agent.run("Check ORD-001 and ORD-002.")
    assert isinstance(
        result,
        AgentResult,
    )

    assert result.answer == ("I checked both orders.")
    assert result.steps == 2
    assert tool.executed_arguments == [
        '{"order_number":"ORD-001"}',
        '{"order_number":"ORD-002"}',
    ]
    assert len(llm.requests) == 3

    second_request = llm.requests[1]
    assert second_request.continuation_id == "response-001"

    third_request = llm.requests[2]
    assert third_request.continuation_id == "response-002"

    assert result.trace.llm_calls == 3
    assert result.trace.tool_calls == 2

    assert len(result.trace.steps) == 2

    assert result.trace.steps[0].step_number == 1

    assert result.trace.steps[1].step_number == 2


@pytest.mark.asyncio
async def test_agent_stops_when_max_steps_exceeded() -> None:
    tool = FakeAgentTool(
        name="get_order",
        output='{"found":true}',
    )

    registry = ToolRegistry(
        tools=[
            tool,
        ]
    )

    executor = ToolExecutor(
        registry=registry,
    )

    llm = FakeLLMGateway(
        results=[
            LLMResult(
                text="",
                tool_calls=[
                    LLMToolCall(
                        call_id="call-001",
                        name="get_order",
                        arguments=('{"order_number":"ORD-001"}'),
                    )
                ],
                continuation_id="response-001",
            ),
            LLMResult(
                text="",
                tool_calls=[
                    LLMToolCall(
                        call_id="call-002",
                        name="get_order",
                        arguments=('{"order_number":"ORD-002"}'),
                    )
                ],
                continuation_id="response-002",
            ),
        ]
    )

    agent = OrderAgentService(
        llm=llm,
        registry=registry,
        executor=executor,
        max_steps=1,
    )

    with pytest.raises(AgentMaxStepsExceededError):
        await agent.run("Keep checking orders.")

    assert tool.executed_arguments == ['{"order_number":"ORD-001"}']

    assert len(llm.requests) == 2


@pytest.mark.asyncio
async def test_agent_pauses_before_tool_that_requires_approval() -> None:
    tool = FakeAgentTool(
        name="cancel_order",
        output=('{"ok":true,' '"order_number":"ORD-001",' '"status":"Cancelled"}'),
        requires_approval=True,
    )

    registry = ToolRegistry(
        tools=[
            tool,
        ]
    )

    executor = ToolExecutor(
        registry=registry,
    )

    llm = FakeLLMGateway(
        results=[
            LLMResult(
                text="",
                tool_calls=[
                    LLMToolCall(
                        call_id="call-001",
                        name="cancel_order",
                        arguments=('{"order_number":"ORD-001"}'),
                    )
                ],
                continuation_id="response-001",
            )
        ]
    )

    agent = OrderAgentService(
        llm=llm,
        registry=registry,
        executor=executor,
        max_steps=6,
    )

    result = await agent.run("Cancel ORD-001.")

    assert isinstance(
        result,
        AgentApprovalResult,
    )

    assert len(result.requests) == 1

    approval = result.requests[0]

    assert approval.call_id == "call-001"
    assert approval.tool_name == "cancel_order"

    assert approval.arguments == ('{"order_number":"ORD-001"}')

    assert tool.executed_arguments == []

    assert len(result.state.pending_tool_calls) == 1

    pending_call = result.state.pending_tool_calls[0]

    assert pending_call.call_id == "call-001"

    assert result.state.continuation_id == "response-001"

    assert result.state.trace.llm_calls == 1
    assert result.state.trace.tool_calls == 0
    assert len(result.state.steps) == 0


@pytest.mark.asyncio
async def test_agent_resumes_after_approval() -> None:
    tool = FakeAgentTool(
        name="cancel_order",
        output=('{"ok":true,' '"order_number":"ORD-001",' '"status":"Cancelled"}'),
        requires_approval=True,
    )

    registry = ToolRegistry(
        tools=[
            tool,
        ]
    )

    executor = ToolExecutor(
        registry=registry,
    )

    llm = FakeLLMGateway(
        results=[
            LLMResult(
                text="",
                tool_calls=[
                    LLMToolCall(
                        call_id="call-001",
                        name="cancel_order",
                        arguments=('{"order_number":"ORD-001"}'),
                    )
                ],
                continuation_id="response-001",
            ),
            LLMResult(
                text=("Order ORD-001 was cancelled."),
            ),
        ]
    )

    agent = OrderAgentService(
        llm=llm,
        registry=registry,
        executor=executor,
        max_steps=6,
    )

    paused = await agent.run("Cancel ORD-001.")
    assert isinstance(
        paused,
        AgentApprovalResult,
    )
    assert tool.executed_arguments == []

    result = await agent.resume(
        state=paused.state,
        approved_call_ids={
            "call-001",
        },
        rejected_call_ids=set(),
    )

    assert isinstance(
        result,
        AgentResult,
    )

    assert result.answer == ("Order ORD-001 was cancelled.")

    assert tool.executed_arguments == ['{"order_number":"ORD-001"}']

    assert result.steps == 1

    assert result.trace.llm_calls == 2
    assert result.trace.tool_calls == 1

    assert len(result.trace.steps) == 1

    step_trace = result.trace.steps[0]

    assert step_trace.step_number == 1

    assert step_trace.tool_names == ["cancel_order"]

    assert len(llm.requests) == 2

    second_request = llm.requests[1]

    assert second_request.continuation_id == "response-001"

    assert len(second_request.tool_outputs) == 1

    tool_output = second_request.tool_outputs[0]

    assert tool_output.call_id == "call-001"


@pytest.mark.asyncio
async def test_agent_turns_rejection_into_observation() -> None:
    tool = FakeAgentTool(
        name="cancel_order",
        output=('{"ok":true,' '"order_number":"ORD-001",' '"status":"Cancelled"}'),
        requires_approval=True,
    )

    registry = ToolRegistry(
        tools=[
            tool,
        ]
    )

    executor = ToolExecutor(
        registry=registry,
    )

    llm = FakeLLMGateway(
        results=[
            LLMResult(
                text="",
                tool_calls=[
                    LLMToolCall(
                        call_id="call-001",
                        name="cancel_order",
                        arguments=('{"order_number":"ORD-001"}'),
                    )
                ],
                continuation_id="response-001",
            ),
            LLMResult(
                text=("The cancellation was not performed."),
            ),
        ]
    )

    agent = OrderAgentService(
        llm=llm,
        registry=registry,
        executor=executor,
        max_steps=6,
    )

    paused = await agent.run("Cancel ORD-001.")

    assert isinstance(
        paused,
        AgentApprovalResult,
    )

    assert tool.executed_arguments == []

    result = await agent.resume(
        state=paused.state,
        approved_call_ids=set(),
        rejected_call_ids={
            "call-001",
        },
    )

    assert tool.executed_arguments == []

    assert isinstance(
        result,
        AgentResult,
    )

    assert result.answer == ("The cancellation was not performed.")

    assert len(llm.requests) == 2

    second_request = llm.requests[1]

    assert len(second_request.tool_outputs) == 1

    tool_output = second_request.tool_outputs[0]

    assert tool_output.call_id == "call-001"

    output = json.loads(tool_output.output)

    assert output["ok"] is False

    assert output["error_code"] == "USER_REJECTED"

    assert output["message"] == "The user rejected this action."

    assert result.steps == 1

    assert result.trace.llm_calls == 2

    assert result.trace.tool_calls == 1


@pytest.mark.asyncio
async def test_agent_reuses_conversation_history() -> None:
    registry = ToolRegistry(tools=[])

    executor = ToolExecutor(registry=registry)

    llm = FakeLLMGateway(
        results=[
            LLMResult(
                text="ORD-001 is pending.",
            ),
            LLMResult(
                text=("Yes, I remember " "you were asking about ORD-001."),
            ),
        ]
    )

    agent = OrderAgentService(
        llm=llm,
        registry=registry,
        executor=executor,
        max_steps=6,
    )

    first_result = await agent.run("What is the status of ORD-001?")

    assert isinstance(
        first_result,
        AgentResult,
    )

    assert len(first_result.conversation.messages) == 2
    assert (
        first_result.conversation.messages[0].content
        == "What is the status of ORD-001?"
    )
    assert first_result.conversation.messages[1].content == "ORD-001 is pending."

    second_result = await agent.run(
        "Do you remember it?",
        conversation=(first_result.conversation),
    )

    assert isinstance(
        second_result,
        AgentResult,
    )

    assert len(llm.requests) == 2
    second_request = llm.requests[1]
    assert len(second_request.messages) == 3
    assert second_request.messages[0].content == "What is the status of ORD-001?"

    assert second_request.messages[1].content == "ORD-001 is pending."

    assert second_request.messages[2].content == "Do you remember it?"

    assert len(second_result.conversation.messages) == 4

    assert second_result.conversation.messages[-1].content == (
        "Yes, I remember " "you were asking about ORD-001."
    )
