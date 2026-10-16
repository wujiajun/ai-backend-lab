import json
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from typing import Protocol

from ai_backend_lab.application.exceptions import (
    LLMOutputError,
)


@dataclass(frozen=True)
class ToolExecutionContext:
    run_id: str


class ToolExecutionStatus(StrEnum):
    STARTED = "started"
    COMPLETED = "completed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ToolExecutionRecord:
    run_id: str
    call_id: str
    tool_name: str
    intent_hash: str

    status: ToolExecutionStatus

    output: str | None = None


class ToolExecutionStore(Protocol):
    async def get(
        self,
        run_id: str,
        call_id: str,
    ) -> ToolExecutionRecord | None: ...

    async def create(
        self,
        record: ToolExecutionRecord,
    ) -> None: ...

    async def complete(
        self,
        run_id: str,
        call_id: str,
        output: str,
    ) -> ToolExecutionRecord: ...


def _canonicalize_arguments(
    arguments: str,
) -> str:
    try:
        value = json.loads(arguments)
    except json.JSONDecodeError as exc:
        raise LLMOutputError("LLM returned invalid tool arguments.") from exc

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def build_tool_intent_hash(
    tool_name: str,
    arguments: str,
) -> str:
    canonical_arguments = _canonicalize_arguments(arguments)

    payload = f"{tool_name}\0" f"{canonical_arguments}"

    return sha256(payload.encode("utf-8")).hexdigest()


def build_tool_execution_key(
    run_id: str,
    call_id: str,
) -> str:
    return f"{run_id}:{call_id}"
