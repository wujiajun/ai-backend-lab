from dataclasses import replace

import pytest

from ai_backend_lab.application.order_agent.checkpoint import (
    AgentRunCheckpoint,
    AgentRunStatus,
)
from ai_backend_lab.application.order_agent.exceptions import (
    AgentRunConflictError,
    AgentRunStateError,
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
from ai_backend_lab.application.order_agent.run_service import (
    AgentRunService,
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
)
from tests.fakes.llm import FakeLLMGateway


class FakeAgentRunStore:
    def __init__(self) -> None:
        self.checkpoints: dict[
            str,
            AgentRunCheckpoint,
        ] = {}

    async def create(
        self,
        checkpoint: AgentRunCheckpoint,
    ) -> None:
        self.checkpoints[checkpoint.run_id] = checkpoint

    async def get(
        self,
        run_id: str,
    ) -> AgentRunCheckpoint | None:
        return self.checkpoints.get(run_id)

    async def save(
        self,
        checkpoint: AgentRunCheckpoint,
        expected_version: int,
    ) -> AgentRunCheckpoint:
        current = self.checkpoints.get(checkpoint.run_id)

        if current is None or current.version != expected_version:
            raise AgentRunConflictError("Agent run version conflict.")

        saved = replace(
            checkpoint,
            version=expected_version + 1,
        )

        self.checkpoints[checkpoint.run_id] = saved

        return saved

    async def claim_for_resume(
        self,
        run_id: str,
        expected_version: int,
    ) -> AgentRunCheckpoint:
        current = self.checkpoints.get(run_id)

        if (
            current is None
            or current.version != expected_version
            or current.status != AgentRunStatus.WAITING_FOR_APPROVAL
        ):
            raise AgentRunConflictError("Agent run could not be claimed.")

        claimed = replace(
            current,
            status=AgentRunStatus.RUNNING,
            version=expected_version + 1,
        )

        self.checkpoints[run_id] = claimed

        return claimed


class FakeApprovalTool:
    def __init__(self) -> None:
        self.executed_arguments: list[str] = []

    @property
    def definition(
        self,
    ) -> LLMToolDefinition:
        return LLMToolDefinition(
            name="cancel_order",
            description="Fake cancel order tool.",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        )

    @property
    def policy(
        self,
    ) -> AgentToolPolicy:
        return AgentToolPolicy(
            parallel_safe=False,
            requires_approval=True,
        )

    async def execute(
        self,
        arguments: str,
    ) -> str:
        self.executed_arguments.append(arguments)

        return '{"ok":true,' '"status":"Cancelled"}'


@pytest.mark.asyncio
async def test_start_persists_waiting_for_approval() -> None:
    tool = FakeApprovalTool()

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

    store = FakeAgentRunStore()

    run_service = AgentRunService(
        agent=agent,
        store=store,
    )

    execution = await run_service.start("Cancel ORD-001.")

    assert execution.run_id.startswith("run_")
    assert isinstance(
        execution.result,
        AgentApprovalResult,
    )

    checkpoint = await store.get(execution.run_id)

    assert checkpoint is not None

    assert checkpoint.status == AgentRunStatus.WAITING_FOR_APPROVAL

    assert checkpoint.state is not None

    assert len(checkpoint.state.pending_tool_calls) == 1

    assert checkpoint.state.pending_tool_calls[0].call_id == "call-001"

    assert checkpoint.state.continuation_id == "response-001"

    assert tool.executed_arguments == []

    assert checkpoint.version == 2


@pytest.mark.asyncio
async def test_resume_loads_checkpoint_and_completes_run() -> None:
    tool = FakeApprovalTool()

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

    store = FakeAgentRunStore()

    run_service = AgentRunService(
        agent=agent,
        store=store,
    )

    started = await run_service.start("Cancel ORD-001.")

    assert isinstance(
        started.result,
        AgentApprovalResult,
    )

    run_id = started.run_id

    resumed = await run_service.resume(
        run_id=run_id,
        approved_call_ids={
            "call-001",
        },
        rejected_call_ids=set(),
    )

    assert isinstance(
        resumed.result,
        AgentResult,
    )

    assert resumed.result.answer == ("Order ORD-001 was cancelled.")

    assert resumed.run_id == run_id

    assert tool.executed_arguments == ['{"order_number":"ORD-001"}']

    checkpoint = await store.get(run_id)

    assert checkpoint is not None

    assert checkpoint.status == AgentRunStatus.COMPLETED

    assert checkpoint.answer == ("Order ORD-001 was cancelled.")

    assert checkpoint.state is None

    assert checkpoint.version == 4


@pytest.mark.asyncio
async def test_completed_run_cannot_be_resumed_again() -> None:
    tool = FakeApprovalTool()

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

    store = FakeAgentRunStore()

    run_service = AgentRunService(
        agent=agent,
        store=store,
    )

    started = await run_service.start("Cancel ORD-001.")

    run_id = started.run_id

    await run_service.resume(
        run_id=run_id,
        approved_call_ids={
            "call-001",
        },
        rejected_call_ids=set(),
    )

    assert tool.executed_arguments == ['{"order_number":"ORD-001"}']

    with pytest.raises(AgentRunStateError):
        await run_service.resume(
            run_id=run_id,
            approved_call_ids={
                "call-001",
            },
            rejected_call_ids=set(),
        )

    assert tool.executed_arguments == ['{"order_number":"ORD-001"}']
