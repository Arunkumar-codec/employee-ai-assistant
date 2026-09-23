import pytest
from app.services.session_service import SessionManager, ConversationSession
from app.schemas.chat import ChatRequest

def test_session_creation_and_continuation():
    sm=SessionManager(); s=sm.get_or_create_session(employee_id='EMP001'); assert sm.get_or_create_session(s.conversation_id,'EMP001') is s

def test_unique_and_isolated_sessions():
    sm=SessionManager(); a=sm.get_or_create_session(employee_id='EMP001'); b=sm.get_or_create_session(employee_id='EMP002'); assert a.conversation_id != b.conversation_id

def test_employee_mismatch_rejected():
    sm=SessionManager(); s=sm.get_or_create_session(employee_id='EMP001')
    with pytest.raises(ValueError): sm.get_or_create_session(s.conversation_id,'EMP002')

def test_history_bounded():
    s=ConversationSession(conversation_id='x',max_history_messages=4)
    for i in range(6): s.add_message('user',str(i))
    assert [m.content for m in s.history]==['2','3','4','5']

def test_clear_session():
    sm=SessionManager(); s=sm.get_or_create_session(employee_id='EMP001'); assert sm.clear_session(s.conversation_id); assert sm.get_session(s.conversation_id) is None

def test_chat_request_validation_and_normalization():
    assert ChatRequest(message=' hi ',employee_id=' emp001 ').employee_id=='EMP001'
    with pytest.raises(ValueError): ChatRequest(message='   ',employee_id='EMP001')
