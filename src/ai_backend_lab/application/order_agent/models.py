from dataclasses import dataclass, field

from ai_backend_lab.application.ports.llm import (
    LLMToolCall,
    LLMToolOutput,
)


@dataclass
class AgentStep:
    number: int
    tool_calls: list[LLMToolCall] = field(default_factory=list)
    tool_outputs: list[LLMToolOutput] = field(default_factory=list)


@dataclass
class AgentState:
    user_message: str
    steps: list[AgentStep] = field(default_factory=list)
    continuation_id: str | None = None
    pending_tool_calls: list[LLMToolCall] = field(default_factory=list)


@dataclass(frozen=True)
class AgentResult:
    answer: str
    steps: int


@dataclass(frozen=True)
class AgentApprovalRequest:
    call_id: str
    tool_name: str
    arguments: str


@dataclass(frozen=True)
class AgentApprovalResult:
    state: AgentState
    requests: list[AgentApprovalRequest]


AgentRunResult = AgentResult | AgentApprovalResult
