from typing import Any

from pydantic import TypeAdapter

from ai_backend_lab.application.order_agent.models import (
    AgentState,
)

_AGENT_STATE_ADAPTER = TypeAdapter(AgentState)


def serialize_agent_state(
    state: AgentState,
) -> dict[str, Any]:
    return _AGENT_STATE_ADAPTER.dump_python(
        state,
        mode="json",
    )


def deserialize_agent_state(
    data: dict[str, Any],
) -> AgentState:
    return _AGENT_STATE_ADAPTER.validate_python(data)
