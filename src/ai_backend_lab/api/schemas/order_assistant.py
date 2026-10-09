from pydantic import BaseModel, Field


class OrderAssistantRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
    )


class OrderAssistantResponse(BaseModel):
    answer: str


class AssistantRequest(BaseModel):
    message: str
