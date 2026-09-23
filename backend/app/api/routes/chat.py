"""POST /api/chat with bounded conversation context."""
import logging
from fastapi import APIRouter, HTTPException, status
from app.agent.orchestrator import AgentOrchestrator
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.session_service import session_manager
from app.data.employee_db import db

logger=logging.getLogger(__name__)
router=APIRouter(); orchestrator=AgentOrchestrator()

@router.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        if db.get_employee(request.employee_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        try:
            session=session_manager.get_or_create_session(request.conversation_id, request.employee_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Conversation belongs to another employee')
        result=orchestrator.process_request(request.message, session.employee_id, session.history)
        session.add_message('user', request.message, session.employee_id)
        session.add_message('assistant', result.answer, session.employee_id, result.tools_used, result.sources)
        return ChatResponse(answer=result.answer, sources=result.sources, tools_used=result.tools_used, conversation_id=session.conversation_id)
    except HTTPException: raise
    except Exception:
        logger.exception('Unexpected error while processing chat request')
        raise HTTPException(status_code=500, detail='An internal error occurred while processing the request.')

@router.delete('/chat/{conversation_id}')
def clear_chat(conversation_id: str):
    if not session_manager.clear_session(conversation_id): raise HTTPException(status_code=404, detail='Conversation session not found.')
    return {'message':'Conversation cleared.'}
