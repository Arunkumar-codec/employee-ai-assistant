"""
Chat endpoint.

WHAT: POST /api/chat — accepts {employee_id, message}, returns
      {answer, sources, tools_used} per the assessment's API contract.
WHY:  Day 1 goal is API *stability*, not a working AI. The RAG pipeline
      (Day 2-3) and agent/tool logic (Day 4) do not exist yet, so this
      route must not fabricate a real answer.
HOW:  Returns a clearly-labeled "not implemented yet" response using the
      same response schema the real implementation will use later, so the
      frontend contract never has to change.
"""
from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

_NOT_IMPLEMENTED_MESSAGE = (
    "This assistant is not implemented yet (Day 1 foundation). "
    "The RAG pipeline is planned for Day 2-3 and the agent/tools for Day 4. "
    "This response is a development stub, not a real answer."
)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    # Intentionally no RAG / LLM / agent logic yet — see docstring above.
    return ChatResponse(
        answer=_NOT_IMPLEMENTED_MESSAGE,
        sources=[],
        tools_used=[],
    )
