from typing import Any, Dict, Optional

from app.services.rag_service import answer_question
from app.tools.employee_tools import apply_leave, get_employee_info


class ToolsRegistry:
    """Thin registry around the existing Phase 2 RAG and Phase 3 employee tools."""

    def search_company_documents(self, query: str) -> Dict[str, Any]:
        result = answer_question(query)
        return {"answer": result.answer, "sources": result.sources}

    def execute_get_employee_info(self, employee_id: str) -> Dict[str, Any]:
        return get_employee_info(employee_id)

    def execute_apply_leave(self, employee_id: str, start_date: str, end_date: str, reason: str) -> Dict[str, Any]:
        return apply_leave(employee_id, start_date, end_date, reason)
