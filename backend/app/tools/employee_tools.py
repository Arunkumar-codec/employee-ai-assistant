import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from ..data.employee_db import db


def get_employee_info(employee_id: str) -> Dict[str, Any]:
    if not employee_id or not isinstance(employee_id, str) or not employee_id.strip():
        return {
            "found": False,
            "error": "A valid, non-empty employee ID must be provided.",
            "employee_id": str(employee_id) if employee_id is not None else ""
        }

    cleaned_id = employee_id.strip().upper()
    emp = db.get_employee(cleaned_id)

    if not emp:
        return {
            "found": False,
            "error": f"Employee with ID '{cleaned_id}' was not found.",
            "employee_id": cleaned_id
        }

    return {
        "found": True,
        "employee_id": emp["employee_id"],
        "name": emp["name"],
        "department": emp["department"],
        "leave_balance": emp["leave_balance"],
        "email": emp.get("email", "")
    }


def _parse_date(date_str: str):
    if not date_str or not isinstance(date_str, str):
        return None
    cleaned = date_str.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def apply_leave(employee_id: str, start_date: str, end_date: str, reason: str) -> Dict[str, Any]:
    if not employee_id or not isinstance(employee_id, str) or not employee_id.strip():
        return {"status": "failure", "message": "A valid, non-empty employee ID is required."}

    cleaned_id = employee_id.strip().upper()
    emp = db.get_employee(cleaned_id)
    if not emp:
        return {
            "status": "failure",
            "message": f"Leave application failed: Employee ID '{cleaned_id}' not found."
        }

    if not reason or not isinstance(reason, str) or not reason.strip():
        return {
            "status": "failure",
            "message": "Leave application failed: A valid, non-empty reason must be provided."
        }

    parsed_start = _parse_date(start_date)
    parsed_end = _parse_date(end_date)

    if not parsed_start or not parsed_end:
        return {
            "status": "failure",
            "message": "Leave application failed: Invalid date format. Please use YYYY-MM-DD format (e.g., 2026-09-20)."
        }

    if parsed_end < parsed_start:
        return {
            "status": "failure",
            "message": f"Leave application failed: End date ({end_date}) cannot be earlier than start date ({start_date})."
        }

    days_requested = (parsed_end - parsed_start).days + 1
    current_balance = emp["leave_balance"]

    if days_requested > current_balance:
        return {
            "status": "failure",
            "message": f"Leave application failed: Insufficient leave balance. Requested {days_requested} day(s), but only {current_balance} day(s) available."
        }

    new_balance = current_balance - days_requested
    app_id = f"LEAVE-{uuid.uuid4().hex[:8].upper()}"

    db_record = {
        "application_id": app_id,
        "employee_id": cleaned_id,
        "employee_name": emp["name"],
        "start_date": str(parsed_start),
        "end_date": str(parsed_end),
        "reason": reason.strip(),
        "days_requested": days_requested,
        "status": "APPROVED",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    if not db.commit_leave_application(cleaned_id, db_record, new_balance):
        return {"status": "failure", "message": "Leave application failed: employee state changed before commit."}

    return {
        "status": "success",
        "message": f"Leave application submitted successfully. Approved {days_requested} day(s) for {emp['name']} ({cleaned_id}) from {parsed_start} to {parsed_end}.",
        "application_id": app_id,
        "days_requested": days_requested,
        "remaining_balance": new_balance,
        "employee_id": cleaned_id
    }
