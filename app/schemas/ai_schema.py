from pydantic import BaseModel
from typing import Optional


class AIChatRequest(BaseModel):
    user_id: str
    message: str


class AIChatResponse(BaseModel):
    reply: str
    session_id: Optional[str] = None