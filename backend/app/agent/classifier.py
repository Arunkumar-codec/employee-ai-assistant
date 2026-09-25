import json
import re
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.core.config import settings
from app.services.llm_service import LLMProvider, get_llm_service


class IntentEnum(str, Enum):
    RAG_ONLY = "RAG_ONLY"
    EMPLOYEE_INFO = "EMPLOYEE_INFO"
    RAG_AND_EMPLOYEE_INFO = "RAG_AND_EMPLOYEE_INFO"
    APPLY_LEAVE = "APPLY_LEAVE"


class StructuredIntentOutput(BaseModel):
    intent: IntentEnum
    employee_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    reason: Optional[str] = None


def normalize_date_string(
    date_str: Optional[str],
    default_year: int = 2026,
) -> Optional[str]:
    if not date_str:
        return None

    cleaned = date_str.strip()

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", cleaned):
        try:
            datetime.strptime(cleaned, "%Y-%m-%d")
            return cleaned
        except ValueError:
            return None

    if re.fullmatch(r"\d{1,2}[/-]\d{1,2}[/-]\d{4}", cleaned):
        for fmt in ("%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    months = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }

    match = re.search(
        r"(\d{1,2})\s+([A-Za-z]+)(?:\s+(\d{4}))?",
        cleaned,
        re.IGNORECASE,
    )

    if not match:
        return None

    day = int(match.group(1))
    month = months.get(match.group(2).lower())
    year = int(match.group(3)) if match.group(3) else default_year

    if not month:
        return None

    try:
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return None


class IntentClassifier:
    """
    LLM-assisted intent and parameter extraction with deterministic
    routing for important employee-assistant cases.
    """

    def __init__(
        self,
        llm_service: Optional[LLMProvider] = None,
    ):
        self.llm_service = llm_service or get_llm_service(
            settings.llm_provider,
            settings.llm_model,
            settings.llm_api_key,
            settings.llm_fallback_api_key,
        )

    def classify(
        self,
        message: str,
        explicit_employee_id: Optional[str] = None,
    ) -> StructuredIntentOutput:
        msg_lower = message.lower()

        apply_signals = [
            "apply leave",
            "apply for leave",
            "request leave",
            "book leave",
            "take leave",
            "submit leave",
        ]

        has_leave_action = any(signal in msg_lower for signal in apply_signals) or bool(
            re.search(r"\b(?:i\s+)?(?:want|need|would like|give me)\b.{0,30}\bleave\b", msg_lower)
        )

        if has_leave_action:
            return self._classify_fallback(
                message,
                explicit_employee_id,
            )

        policy_signals = [
            "policy",
            "allowed",
            "allowance",
            "rules",
            "benefits",
            "insurance",
            "reimbursement",
            "faq",
            "wfh",
            "work from home",
            "remote work",
            "travel policy",
        ]

        personal_leave_signals = [
            "leave balance",
            "my leaves",
            "leaves do i have",
            "leaves do i have left",
            "leaves remaining",
            "remaining leaves",
            "my leave balance",
        ]

        is_policy_question = any(
            signal in msg_lower
            for signal in policy_signals
        )

        is_personal_question = any(
            signal in msg_lower
            for signal in personal_leave_signals
        )

        if is_policy_question and not is_personal_question:
            return StructuredIntentOutput(
                intent=IntentEnum.RAG_ONLY,
                employee_id=explicit_employee_id,
            )

        if is_policy_question and is_personal_question:
            return StructuredIntentOutput(
                intent=IntentEnum.RAG_AND_EMPLOYEE_INFO,
                employee_id=explicit_employee_id,
            )

        llm_result = self._classify_with_llm(
            message,
            explicit_employee_id,
        )

        if llm_result is not None:
            return llm_result

        return self._classify_fallback(
            message,
            explicit_employee_id,
        )

    def _classify_with_llm(
        self,
        message: str,
        explicit_employee_id: Optional[str],
    ) -> Optional[StructuredIntentOutput]:
        system_prompt = """
You classify Employee AI Assistant requests and extract parameters.

Return ONLY one valid JSON object with keys:
intent, employee_id, start_date, end_date, reason.

Allowed intents:
RAG_ONLY
EMPLOYEE_INFO
RAG_AND_EMPLOYEE_INFO
APPLY_LEAVE

Rules:

RAG_ONLY:
Use for company policy or document questions.

EMPLOYEE_INFO:
Use for employee-specific information such as employee details
or the employee's current leave balance.

RAG_AND_EMPLOYEE_INFO:
Use when the request requires both company-document information
and employee-specific information.

APPLY_LEAVE:
Use only when the user explicitly asks to apply, request, book,
take, or submit leave.

Important distinction:
"How many annual leaves are allowed?" is a company policy question
and should be RAG_ONLY.

"How many leaves do I have?" is an employee-specific balance
question and should be EMPLOYEE_INFO.

Never invent missing values.
Use null for missing employee_id, dates, or reason.
""".strip()

        user_message = (
            f"User query: {message}\n"
            f"Explicit request employee_id: "
            f"{explicit_employee_id or ''}"
        )

        try:
            response_text = self.llm_service.generate(
                system_prompt,
                user_message,
            )

            match = re.search(
                r"\{.*\}",
                response_text,
                re.DOTALL,
            )

            if not match:
                return None

            data = json.loads(match.group(0))

            if not data.get("employee_id") and explicit_employee_id:
                data["employee_id"] = explicit_employee_id

            reason = data.get("reason")
            if reason and str(reason).strip().lower() not in message.lower():
                data["reason"] = None

            data["start_date"] = normalize_date_string(
                data.get("start_date")
            )

            data["end_date"] = normalize_date_string(
                data.get("end_date")
            )

            return StructuredIntentOutput(**data)

        except Exception:
            return None

    def _classify_fallback(
        self,
        message: str,
        explicit_employee_id: Optional[str],
    ) -> StructuredIntentOutput:
        msg_lower = message.lower()

        emp_match = re.search(
            r"\b(EMP\d{3})\b",
            message,
            re.IGNORECASE,
        )

        emp_id = (
            emp_match.group(1).upper()
            if emp_match
            else explicit_employee_id
        )

        is_apply = any(
            keyword in msg_lower
            for keyword in [
                "apply leave", "apply for leave", "request leave",
                "book leave", "take leave", "submit leave",
            ]
        ) or bool(re.search(r"\b(?:i\s+)?(?:want|need|would like|give me)\b.{0,30}\bleave\b", msg_lower))

        is_emp_info = any(
            keyword in msg_lower
            for keyword in [
                "how many leaves",
                "leave balance",
                "my leaves",
                "leaves do i have",
                "employee info",
                "leaves remaining",
                "remaining leaves",
                "check emp",
            ]
        )

        is_rag = any(
            keyword in msg_lower
            for keyword in [
                "policy",
                "faq",
                "rules",
                "allowance",
                "allowed",
                "reimbursement",
                "benefits",
                "insurance",
                "wfh",
                "work from home",
                "travel policy",
                "remote work",
            ]
        )

        if is_apply:
            month_names = (
                r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
                r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?|tember)?|"
                r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
            )
            dates = re.findall(
                rf"\b("
                rf"\d{{1,2}}\s+(?:{month_names})(?:\s+\d{{4}})?"
                rf"|\d{{4}}-\d{{2}}-\d{{2}}"
                rf"|\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{4}}"
                rf")\b",
                message,
                re.IGNORECASE,
            )

            reason = None

            because = re.search(
                r"\bbecause(?:\s+of)?\s+(.+)$",
                message,
                re.IGNORECASE,
            )

            reason_tag = re.search(
                r"\breason\s*:\s*(.+)$",
                message,
                re.IGNORECASE,
            )

            if because:
                reason = because.group(1).strip()

            elif reason_tag:
                reason = reason_tag.group(1).strip()

            else:
                for_reason = re.search(
                    r"\bfor\s+(.+?)(?:\s+reasons?)?[.!]?$",
                    message,
                    re.IGNORECASE,
                )

                if for_reason:
                    reason = for_reason.group(1).strip()

                    reason = re.sub(
                        r"\s+reasons?$",
                        "",
                        reason,
                        flags=re.IGNORECASE,
                    ).strip()

            return StructuredIntentOutput(
                intent=IntentEnum.APPLY_LEAVE,
                employee_id=emp_id,
                start_date=normalize_date_string(
                    dates[0] if len(dates) > 0 else None
                ),
                end_date=normalize_date_string(
                    dates[1] if len(dates) > 1 else None
                ),
                reason=reason,
            )

        if is_rag and is_emp_info:
            return StructuredIntentOutput(
                intent=IntentEnum.RAG_AND_EMPLOYEE_INFO,
                employee_id=emp_id,
            )

        if is_emp_info or (emp_id and not is_rag):
            return StructuredIntentOutput(
                intent=IntentEnum.EMPLOYEE_INFO,
                employee_id=emp_id,
            )

        return StructuredIntentOutput(
            intent=IntentEnum.RAG_ONLY,
            employee_id=emp_id,
        )