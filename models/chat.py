from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    prompt: str
    session_id: str
    tag: str = "general"