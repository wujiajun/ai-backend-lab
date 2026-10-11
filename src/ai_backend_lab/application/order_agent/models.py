from dataclasses import dataclass, field

from ai_backend_lab.application.ports.llm import (
    LLMMessage,
    LLMToolCall,
    LLMToolOutput,
)


@dataclass
class ConversationState:
    messages: list[LLMMessage] = field(default_factory=list)


@dataclass
class AgentStep:
    number: int
    tool_calls: list[LLMToolCall] = field(default_factory=list)
    tool_outputs: list[LLMToolOutput] = field(default_factory=list)


@dataclass
class AgentState:
    user_message: str
    conversation: ConversationState
    steps: list[AgentStep] = field(default_factory=list)
    continuation_id: str | None = None
    pending_tool_calls: list[LLMToolCall] = field(default_factory=list)


@dataclass(frozen=True)
class AgentResult:
    answer: str
    steps: int
    conversation: ConversationState


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


@dataclass(frozen=True)
class AgentStartedEvent:
    pass


@dataclass(frozen=True)
class AgentToolCalledEvent:
    call_id: str
    tool_name: str
    arguments: str


@dataclass(frozen=True)
class AgentToolCompletedEvent:
    call_id: str
    output: str


@dataclass(frozen=True)
class AgentApprovalRequiredEvent:
    requests: list[AgentApprovalRequest]


@dataclass(frozen=True)
class AgentAnswerEvent:
    answer: str


@dataclass(frozen=True)
class AgentCompletedEvent:
    result: AgentResult


AgentEvent = (
    AgentStartedEvent
    | AgentToolCalledEvent
    | AgentToolCompletedEvent
    | AgentApprovalRequiredEvent
    | AgentAnswerEvent
    | AgentCompletedEvent
)
