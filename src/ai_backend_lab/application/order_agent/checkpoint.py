from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from ai_backend_lab.application.order_agent.models import (
    AgentRunResult,
    AgentState,
)


class AgentRunStatus(StrEnum):
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentRunCheckpoint:
    run_id: str
    status: AgentRunStatus
    state: AgentState | None
    answer: str | None = None
    version: int = 1


@dataclass(frozen=True)
class AgentRunExecutionResult:
    run_id: str
    result: AgentRunResult


class AgentRunStore(Protocol):
    async def create(
        self,
        checkpoint: AgentRunCheckpoint,
    ) -> None: ...

    async def get(
        self,
        run_id: str,
    ) -> AgentRunCheckpoint | None: ...

    async def save(
        self,
        checkpoint: AgentRunCheckpoint,
        expected_version: int,
    ) -> AgentRunCheckpoint: ...

    async def claim_for_resume(
        self,
        run_id: str,
        expected_version: int,
    ) -> AgentRunCheckpoint: ...
