from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class ChatRequest(BaseModel):
    employee_id: str = Field(..., min_length=1, examples=["EMP001"])
    message: str = Field(..., examples=["How many leaves do I have?"])
    conversation_id: Optional[str] = None
    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip(): raise ValueError("Message must not be empty.")
        return v.strip()
    @field_validator("employee_id")
    @classmethod
    def normalize_employee_id(cls, v):
        if not v or not v.strip(): raise ValueError("Employee ID must not be empty.")
        return v.strip().upper()

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    conversation_id: Optional[str] = None
