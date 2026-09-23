from typing import Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str
    content: str
    employee_id: Optional[str] = None
    tools_used: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)

class ConversationSession(BaseModel):
    conversation_id: str
    employee_id: Optional[str] = None
    history: List[ChatMessage] = Field(default_factory=list)
    max_history_messages: int = 20
    def add_message(self, role: str, content: str, employee_id: Optional[str]=None, tools_used=None, sources=None):
        if self.employee_id is None and employee_id:
            self.employee_id = employee_id.strip().upper()
        self.history.append(ChatMessage(role=role, content=content, employee_id=employee_id or self.employee_id, tools_used=tools_used or [], sources=sources or []))
        self.history = self.history[-self.max_history_messages:]

class SessionManager:
    def __init__(self): self._sessions: Dict[str, ConversationSession] = {}
    def get_or_create_session(self, conversation_id: Optional[str]=None, employee_id: Optional[str]=None):
        emp = employee_id.strip().upper() if employee_id and employee_id.strip() else None
        if conversation_id and conversation_id in self._sessions:
            session = self._sessions[conversation_id]
            if session.employee_id and emp and session.employee_id != emp:
                raise ValueError("EMPLOYEE_MISMATCH")
            if session.employee_id is None and emp: session.employee_id = emp
            return session
        session = ConversationSession(conversation_id=str(uuid.uuid4()), employee_id=emp)
        self._sessions[session.conversation_id] = session
        return session
    def get_session(self, conversation_id): return self._sessions.get(conversation_id)
    def clear_session(self, conversation_id): return self._sessions.pop(conversation_id, None) is not None
    def clear_all(self): self._sessions.clear()

session_manager = SessionManager()
