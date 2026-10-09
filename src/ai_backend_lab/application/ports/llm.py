from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMRole(StrEnum):
    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class LLMMessage:
    role: LLMRole
    content: str


@dataclass(frozen=True)
class LLMUsage:
    input_tokens: int
    output_tokens: int
    cached_tokens: int = 0
    reasoning_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class StructuredLLMResult(Generic[T]):
    value: T
    usage: LLMUsage | None = None
    status: str | None = None
    incomplete_reason: str | None = None


@dataclass(frozen=True)
class LLMToolDefinition:
    name: str
    description: str
    parameters: dict[str, object]


@dataclass(frozen=True)
class LLMToolCall:
    call_id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class LLMToolOutput:
    call_id: str
    output: str


@dataclass(frozen=True)
class LLMRequest:
    instructions: str | None = None
    messages: list[LLMMessage] = field(default_factory=list)
    tools: list[LLMToolDefinition] = field(default_factory=list)
    continuation_id: str | None = None
    tool_outputs: list[LLMToolOutput] = field(default_factory=list)


@dataclass(frozen=True)
class LLMResult:
    text: str
    usage: LLMUsage | None = None
    status: str | None = None
    incomplete_reason: str | None = None
    tool_calls: list[LLMToolCall] = field(default_factory=list)
    continuation_id: str | None = None


class LLMGateway(Protocol):
    async def generate(self, request: LLMRequest) -> LLMResult: ...

    async def generate_structured(
        self,
        request: LLMRequest,
        output_type: type[T],
    ) -> StructuredLLMResult[T]: ...

    def stream(
        self,
        request: LLMRequest,
    ) -> AsyncIterator[str]: ...
