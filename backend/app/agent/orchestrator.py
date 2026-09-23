import re
from typing import Optional

from app.agent.classifier import IntentClassifier, IntentEnum
from app.agent.tools_registry import ToolsRegistry
from app.schemas.chat import ChatResponse
from app.services.session_service import ChatMessage


def _build_rag_query_for_combined(message: str) -> str:
    """Remove the employee-info sub-question before sending a mixed request to RAG.

    The agent has already classified the request as RAG_AND_EMPLOYEE_INFO, so the
    employee-specific part is handled by get_employee_info(). Keeping that part in
    the vector-search query can dilute semantic relevance and trigger a false
    no-answer even when the policy portion is well supported.
    """
    query = message.strip()

    employee_clauses = [
        r"\s+(?:and|also)\s+how\s+many\s+leaves\s+does\s+EMP\d{3}\s+have\s*[?.!]*$",
        r"\s+(?:and|also)\s+(?:what\s+is\s+)?(?:the\s+)?leave\s+balance(?:\s+for)?\s+EMP\d{3}\s*[?.!]*$",
        r"\s+(?:and|also)\s+EMP\d{3}\s+(?:leave\s+balance|leaves\s+remaining)\s*[?.!]*$",
    ]
    for pattern in employee_clauses:
        reduced = re.sub(pattern, "", query, flags=re.IGNORECASE).strip()
        if reduced != query:
            query = reduced
            break

    # Safe fallback for less common wording: remove only clearly employee-info
    # phrases, never policy/document terms.
    query = re.sub(
        r"\bhow\s+many\s+leaves\s+does\s+EMP\d{3}\s+have\b",
        "",
        query,
        flags=re.IGNORECASE,
    )
    query = re.sub(
        r"\b(?:leave\s+balance|leaves\s+remaining)\s+(?:for\s+)?EMP\d{3}\b",
        "",
        query,
        flags=re.IGNORECASE,
    )
    query = re.sub(r"\s+(?:and|also)\s*[?.!]*$", "", query, flags=re.IGNORECASE)
    query = re.sub(r"\s{2,}", " ", query).strip(" ,;:-")

    # Never turn a valid mixed request into an empty RAG query.
    return query or message.strip()


class AgentOrchestrator:
    def __init__(self, tools_registry: Optional[ToolsRegistry] = None, classifier: Optional[IntentClassifier] = None):
        self.registry = tools_registry or ToolsRegistry()
        self.classifier = classifier or IntentClassifier()

    def process_request(self, message: str, explicit_employee_id: Optional[str] = None, history: Optional[list[ChatMessage]] = None) -> ChatResponse:
        # History resolves referents only; mutable employee state always comes from tools.
        context = " ".join(m.content for m in (history or [])[-6:])
        effective_message = message
        lower = message.lower()
        if history and not re.search(r"\bEMP\d{3}\b", message, re.I):
            if any(x in lower for x in ["how many do i have", "how many leaves do i have", "remaining now", "after applying"]):
                effective_message = message + " leave balance"
        classification = self.classifier.classify(effective_message, explicit_employee_id)
        emp_id = classification.employee_id or explicit_employee_id

        if classification.intent == IntentEnum.RAG_ONLY:
            rag = self.registry.search_company_documents(message)
            return ChatResponse(answer=rag["answer"], sources=rag["sources"], tools_used=["search_company_documents"])

        if classification.intent == IntentEnum.EMPLOYEE_INFO:
            if not emp_id:
                return ChatResponse(answer="Please specify a valid Employee ID (e.g. EMP001) to check employee information.", sources=[], tools_used=[])
            emp = self.registry.execute_get_employee_info(emp_id)
            if not emp.get("found"):
                return ChatResponse(answer=f"Error: {emp.get('error', 'Employee not found.')}", sources=[], tools_used=["get_employee_info"])
            return ChatResponse(answer=f"Employee {emp['name']} ({emp['employee_id']}) from {emp['department']} department has {emp['leave_balance']} leaves remaining.", sources=[], tools_used=["get_employee_info"])

        if classification.intent == IntentEnum.RAG_AND_EMPLOYEE_INFO:
            rag_query = _build_rag_query_for_combined(message)
            rag = self.registry.search_company_documents(rag_query)
            parts = [rag["answer"]]
            tools = ["search_company_documents"]
            if emp_id:
                tools.append("get_employee_info")
                emp = self.registry.execute_get_employee_info(emp_id)
                if emp.get("found"):
                    parts.append(f"Employee {emp['name']} ({emp['employee_id']}) has {emp['leave_balance']} leaves remaining.")
                else:
                    parts.append(f"Employee Info: {emp.get('error', 'Employee not found.')}")
            else:
                parts.append("Please specify an Employee ID to check leave balance.")
            return ChatResponse(answer="\n".join(parts), sources=rag["sources"], tools_used=tools)

        if classification.intent == IntentEnum.APPLY_LEAVE:
            if explicit_employee_id and classification.employee_id and classification.employee_id.upper() != explicit_employee_id.upper():
                return ChatResponse(answer="Employee context mismatch. You cannot apply leave for a different employee in this session.", sources=[], tools_used=[])
            missing = []
            if not emp_id: missing.append("Employee ID")
            if not classification.start_date: missing.append("start date")
            if not classification.end_date: missing.append("end date")
            if not classification.reason: missing.append("reason for leave")
            if missing:
                return ChatResponse(answer=f"To apply for leave, please provide the following missing detail(s): {', '.join(missing)}.", sources=[], tools_used=[])

            emp = self.registry.execute_get_employee_info(emp_id)
            tools = ["get_employee_info"]
            if not emp.get("found"):
                return ChatResponse(answer=f"Leave application failed: {emp.get('error', 'Employee not found.')}", sources=[], tools_used=tools)
            tools.append("apply_leave")
            result = self.registry.execute_apply_leave(emp_id, classification.start_date, classification.end_date, classification.reason)
            if result.get("status") == "failure":
                return ChatResponse(answer=f"Leave application failed for {emp['name']}: {result.get('message')}", sources=[], tools_used=tools)
            return ChatResponse(answer=f"{result.get('message')} Updated leave balance for {emp['name']}: {result.get('remaining_balance')} days remaining.", sources=[], tools_used=tools)

        return ChatResponse(answer="I couldn't process your request.", sources=[], tools_used=[])
