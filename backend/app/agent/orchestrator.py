import re
from datetime import date
from typing import Optional

from app.agent.classifier import IntentClassifier, IntentEnum
from app.agent.tools_registry import ToolsRegistry
from app.schemas.chat import ChatResponse
from app.services.session_service import ChatMessage

_RAG_SIGNALS = (
    "policy", "allowed", "allowance", "rules", "benefits", "insurance",
    "reimbursement", "faq", "wfh", "work from home", "remote work", "travel policy",
)
_EMPLOYEE_SIGNALS = (
    "leave balance", "my leaves", "leaves do i have", "leaves do i have left",
    "leaves i have", "leaves i have left", "leaves remaining", "remaining leaves",
    "my leave balance", "my name", "tell me my name", "employee info",
)


def _has_leave_action(message: str) -> bool:
    text = message.lower()
    direct = ("apply leave", "apply for leave", "request leave", "book leave", "take leave", "submit leave")
    return any(x in text for x in direct) or bool(
        re.search(r"\b(?:i\s+)?(?:want|need|would like|give me)\b.{0,30}\bleave\b", text)
    )


def _build_rag_query_for_combined(message: str) -> str:
    clauses = re.split(r"[,;]|\b(?:also|and)\b", message, flags=re.IGNORECASE)
    rag_clauses = [c.strip(" .?!") for c in clauses if any(s in c.lower() for s in _RAG_SIGNALS)]
    if rag_clauses:
        return " ".join(rag_clauses).strip()

    query = re.sub(r"\bhow\s+many\s+leaves\s+does\s+EMP\d{3}\s+have\b", "", message, flags=re.I)
    query = re.sub(r"\b(?:leave\s+balance|leaves\s+remaining)\s+(?:for\s+)?EMP\d{3}\b", "", query, flags=re.I)
    query = re.sub(r"\s{2,}", " ", query).strip(" ,;:-")
    return query or message.strip()


def _stated_leave_days(message: str) -> Optional[int]:
    match = re.search(r"\b(\d{1,3})\s+days?\s+(?:of\s+)?leave\b|\bleave\s+(?:for\s+)?(\d{1,3})\s+days?\b", message, re.I)
    if not match:
        return None
    return int(match.group(1) or match.group(2))


def _duration_mismatch(message: str, start_date: Optional[str], end_date: Optional[str]) -> Optional[str]:
    stated = _stated_leave_days(message)
    if stated is None or not start_date or not end_date:
        return None
    try:
        calculated = (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days + 1
    except ValueError:
        return None
    if stated != calculated:
        return (
            f"You requested {stated} day(s), but the dates {start_date} to {end_date} "
            f"cover {calculated} calendar day(s). Please correct either the number of days or the dates."
        )
    return None


class AgentOrchestrator:
    def __init__(self, tools_registry: Optional[ToolsRegistry] = None, classifier: Optional[IntentClassifier] = None):
        self.registry = tools_registry or ToolsRegistry()
        self.classifier = classifier or IntentClassifier()

    def process_request(self, message: str, explicit_employee_id: Optional[str] = None, history: Optional[list[ChatMessage]] = None) -> ChatResponse:
        effective_message = message
        lower = message.lower()

        if history and not re.search(r"\bEMP\d{3}\b", message, re.I):
            if any(x in lower for x in ("how many do i have", "how many leaves do i have", "remaining now", "after applying")):
                effective_message += " leave balance"

            # Complete a pending leave request from the immediately preceding
            # conversation turns. This keeps the scope narrow: history is only
            # reused when the assistant explicitly asked for missing leave fields.
            last_assistant = next((m for m in reversed(history) if m.role == "assistant"), None)
            if last_assistant and "to apply for leave, please provide" in last_assistant.content.lower():
                prior_leave = next(
                    (m.content for m in reversed(history) if m.role == "user" and _has_leave_action(m.content)),
                    None,
                )
                if prior_leave and not _has_leave_action(message):
                    effective_message = f"{prior_leave}; {message}"

        effective_lower = effective_message.lower()
        has_rag = any(s in effective_lower for s in _RAG_SIGNALS)
        has_employee = any(s in effective_lower for s in _EMPLOYEE_SIGNALS)
        has_action = _has_leave_action(effective_message)
        if sum((has_rag, has_employee, has_action)) >= 2:
            return self._process_compound(effective_message, explicit_employee_id, has_rag, has_employee, has_action)

        classification = self.classifier.classify(effective_message, explicit_employee_id)
        emp_id = classification.employee_id or explicit_employee_id

        if classification.intent == IntentEnum.RAG_ONLY:
            rag = self.registry.search_company_documents(message)
            return ChatResponse(answer=rag["answer"], sources=rag["sources"], tools_used=["search_company_documents"])

        if classification.intent == IntentEnum.EMPLOYEE_INFO:
            return self._employee_response(emp_id)

        if classification.intent == IntentEnum.RAG_AND_EMPLOYEE_INFO:
            rag = self.registry.search_company_documents(_build_rag_query_for_combined(message))
            employee = self._employee_response(emp_id)
            return ChatResponse(
                answer="\n".join([rag["answer"], employee.answer]),
                sources=rag["sources"],
                tools_used=["search_company_documents"] + employee.tools_used,
            )

        if classification.intent == IntentEnum.APPLY_LEAVE:
            return self._apply_leave_response(effective_message, classification, explicit_employee_id)

        return ChatResponse(answer="I couldn't process your request.", sources=[], tools_used=[])

    def _employee_response(self, employee_id: Optional[str]) -> ChatResponse:
        if not employee_id:
            return ChatResponse(answer="Please specify a valid Employee ID (e.g. EMP001) to check employee information.", sources=[], tools_used=[])
        emp = self.registry.execute_get_employee_info(employee_id)
        if not emp.get("found"):
            return ChatResponse(answer=f"Error: {emp.get('error', 'Employee not found.')}", sources=[], tools_used=["get_employee_info"])
        return ChatResponse(
            answer=f"Employee {emp['name']} ({emp['employee_id']}) from {emp['department']} department has {emp['leave_balance']} leaves remaining.",
            sources=[],
            tools_used=["get_employee_info"],
        )

    def _apply_leave_response(self, message, classification, explicit_employee_id: Optional[str]) -> ChatResponse:
        emp_id = classification.employee_id or explicit_employee_id
        if explicit_employee_id and classification.employee_id and classification.employee_id.upper() != explicit_employee_id.upper():
            return ChatResponse(answer="Employee context mismatch. You cannot apply leave for a different employee in this session.", sources=[], tools_used=[])

        missing = []
        if not emp_id:
            missing.append("Employee ID")
        if not classification.start_date:
            missing.append("start date")
        if not classification.end_date:
            missing.append("end date")
        if not classification.reason:
            missing.append("reason for leave")
        if missing:
            return ChatResponse(answer=f"To apply for leave, please provide the following missing detail(s): {', '.join(missing)}.", sources=[], tools_used=[])

        try:
            start = date.fromisoformat(classification.start_date)
        except ValueError:
            start = None
        if start is not None and start < date.today() and _stated_leave_days(message) is not None:
            return ChatResponse(
                answer=f"Leave application failed: Start date ({classification.start_date}) cannot be in the past.",
                sources=[],
                tools_used=[],
            )

        mismatch = _duration_mismatch(message, classification.start_date, classification.end_date)
        if mismatch:
            return ChatResponse(answer=mismatch, sources=[], tools_used=[])

        emp = self.registry.execute_get_employee_info(emp_id)
        tools = ["get_employee_info"]
        if not emp.get("found"):
            return ChatResponse(answer=f"Leave application failed: {emp.get('error', 'Employee not found.')}", sources=[], tools_used=tools)

        tools.append("apply_leave")
        result = self.registry.execute_apply_leave(emp_id, classification.start_date, classification.end_date, classification.reason)
        if result.get("status") == "failure":
            return ChatResponse(answer=f"Leave application failed for {emp['name']}: {result.get('message')}", sources=[], tools_used=tools)
        return ChatResponse(
            answer=f"{result.get('message')} Updated leave balance for {emp['name']}: {result.get('remaining_balance')} days remaining.",
            sources=[],
            tools_used=tools,
        )

    def _process_compound(self, message: str, employee_id: Optional[str], has_rag: bool, has_employee: bool, has_action: bool) -> ChatResponse:
        answers, sources, tools = [], [], []

        if has_employee:
            employee = self._employee_response(employee_id)
            answers.append(employee.answer)
            tools.extend(employee.tools_used)

        if has_action:
            action = self.classifier.classify(message, employee_id)
            if action.intent != IntentEnum.APPLY_LEAVE:
                action.intent = IntentEnum.APPLY_LEAVE
            leave = self._apply_leave_response(message, action, employee_id)
            answers.append(leave.answer)
            tools.extend(leave.tools_used)

        if has_rag:
            rag = self.registry.search_company_documents(_build_rag_query_for_combined(message))
            answers.append(rag["answer"])
            sources.extend(rag["sources"])
            tools.append("search_company_documents")

        return ChatResponse(
            answer="\n".join(dict.fromkeys(answers)),
            sources=list(dict.fromkeys(sources)),
            tools_used=list(dict.fromkeys(tools)),
        )
