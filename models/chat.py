from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    prompt: str
    session_id: str
    tag: str = "general"

class CollectionCreateRequest(BaseModel):
    name: str
    color: str

class AddSessionToCollectionRequest(BaseModel):
    session_id: str
