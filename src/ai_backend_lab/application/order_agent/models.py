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
    final_answer: str | None = None


@dataclass(frozen=True)
class AgentResult:
    answer: str
    steps: int
