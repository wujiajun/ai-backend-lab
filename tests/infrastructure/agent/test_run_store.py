from collections.abc import Iterator

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session, sessionmaker

from ai_backend_lab.application.order_agent.checkpoint import (
    AgentRunCheckpoint,
    AgentRunStatus,
)
from ai_backend_lab.application.order_agent.exceptions import (
    AgentRunConflictError,
)
from ai_backend_lab.application.order_agent.models import (
    AgentState,
    AgentStep,
    ConversationState,
)
from ai_backend_lab.application.ports.llm import (
    LLMMessage,
    LLMRole,
    LLMToolCall,
    LLMToolOutput,
)
from ai_backend_lab.infrastructure.agent.run_store import (
    SqlAlchemyAgentRunStore,
)
from ai_backend_lab.infrastructure.database.models import (
    AgentRunModel,
)


@pytest.mark.asyncio
async def test_agent_run_store_round_trip(
    uow_session_factory: sessionmaker[Session],
) -> None:
    conversation = ConversationState(
        messages=[
            LLMMessage(
                role=LLMRole.USER,
                content="What is the status of ORD-001?",
            ),
            LLMMessage(
                role=LLMRole.ASSISTANT,
                content="ORD-001 is pending.",
            ),
        ]
    )

    step = AgentStep(
        number=1,
        tool_calls=[
            LLMToolCall(
                call_id="call-001",
                name="get_order",
                arguments=('{"order_number":"ORD-001"}'),
            )
        ],
        tool_outputs=[
            LLMToolOutput(
                call_id="call-001",
                output=('{"found":true,' '"status":"Pending"}'),
            )
        ],
    )

    state = AgentState(
        user_message="Cancel ORD-001.",
        conversation=conversation,
        steps=[
            step,
        ],
        continuation_id="response-002",
        pending_tool_calls=[
            LLMToolCall(
                call_id="call-002",
                name="cancel_order",
                arguments=('{"order_number":"ORD-001"}'),
            )
        ],
        pending_llm_duration_ms=123.45,
    )

    state.trace.llm_calls = 2
    state.trace.tool_calls = 1
    state.trace.input_tokens = 100
    state.trace.output_tokens = 20

    checkpoint = AgentRunCheckpoint(
        run_id="run-test-001",
        status=(AgentRunStatus.WAITING_FOR_APPROVAL),
        state=state,
        version=1,
    )

    store = SqlAlchemyAgentRunStore(
        session_factory=uow_session_factory,
    )
    await store.create(checkpoint)

    loaded = await store.get("run-test-001")

    assert loaded is not None
    assert loaded.run_id == "run-test-001"

    assert loaded.status == AgentRunStatus.WAITING_FOR_APPROVAL

    assert loaded.version == 1
    assert loaded.answer is None

    assert loaded.state is not None

    assert loaded.state.continuation_id == "response-002"

    assert len(loaded.state.pending_tool_calls) == 1

    assert loaded.state.pending_tool_calls[0].name == "cancel_order"

    assert loaded.state.pending_tool_calls[0].call_id == "call-002"

    assert loaded.state.pending_llm_duration_ms == 123.45

    assert len(loaded.state.conversation.messages) == 2

    assert (
        loaded.state.conversation.messages[0].content
        == "What is the status of ORD-001?"
    )

    assert len(loaded.state.steps) == 1

    assert loaded.state.steps[0].number == 1

    assert loaded.state.steps[0].tool_calls[0].name == "get_order"

    assert loaded.state.trace.llm_calls == 2

    assert loaded.state.trace.tool_calls == 1

    assert loaded.state.trace.input_tokens == 100

    assert loaded.state.trace.output_tokens == 20


@pytest.mark.asyncio
async def test_claim_for_resume_uses_optimistic_locking(
    uow_session_factory: sessionmaker[Session],
) -> None:
    store = SqlAlchemyAgentRunStore(
        session_factory=uow_session_factory,
    )

    checkpoint = AgentRunCheckpoint(
        run_id="run-claim-001",
        status=(AgentRunStatus.WAITING_FOR_APPROVAL),
        state=None,
        version=2,
    )

    await store.create(checkpoint)

    claimed = await store.claim_for_resume(
        run_id="run-claim-001",
        expected_version=2,
    )

    assert claimed.status == AgentRunStatus.RUNNING

    assert claimed.version == 3

    with pytest.raises(AgentRunConflictError):
        await store.claim_for_resume(
            run_id="run-claim-001",
            expected_version=2,
        )

    loaded = await store.get("run-claim-001")
    assert loaded is not None
    assert loaded.status == AgentRunStatus.RUNNING
    assert loaded.version == 3


@pytest.fixture(autouse=True)
def clean_agent_runs(
    uow_session_factory: sessionmaker[Session],
) -> Iterator[None]:
    with uow_session_factory() as session:
        session.execute(delete(AgentRunModel))
        session.commit()

    yield

    with uow_session_factory() as session:
        session.execute(delete(AgentRunModel))
        session.commit()
