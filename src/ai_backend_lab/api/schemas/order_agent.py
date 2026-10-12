from typing import Self

from pydantic import BaseModel, Field, model_validator


class AgentRunRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
    )


class AgentApprovalRequestResponse(BaseModel):
    call_id: str
    tool_name: str
    arguments: str


class AgentResumeRequest(BaseModel):
    approved_call_ids: list[str] = Field(default_factory=list)

    rejected_call_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_decisions(self) -> Self:
        approved = set(self.approved_call_ids)

        rejected = set(self.rejected_call_ids)

        if approved & rejected:
            raise ValueError("A tool call cannot be both " "approved and rejected.")

        return self


class AgentRunResponse(BaseModel):
    run_id: str
    status: str
    answer: str | None = None

    approval_requests: list[AgentApprovalRequestResponse] = Field(default_factory=list)
