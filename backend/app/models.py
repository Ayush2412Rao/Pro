from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=800)
    order_id: str | None = Field(default=None, max_length=40)
    session_id: str | None = Field(default=None, max_length=100)


class ChatResponse(BaseModel):
    status: str
    resolution: str | None = None
    message: str
    escalate: bool
    order_summary: str | None = None
    policy_citations: list[str] = []
    next_steps: list[str] = []
    session_id: str
