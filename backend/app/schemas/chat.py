"""
Pydantic schemas for the /api/chat contract.

WHAT: Request/response models matching the assessment's specified JSON shape.
WHY:  Fixing this contract on Day 1 lets the frontend and later agent/RAG
      work (Days 2-5) develop independently against a stable interface.
HOW:  Standard Pydantic BaseModel with type hints; FastAPI uses these for
      request validation and response serialization/OpenAPI docs.
"""
from typing import List

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    employee_id: str = Field(..., examples=["EMP001"])
    message: str = Field(..., examples=["How many leaves do I have?"])


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
