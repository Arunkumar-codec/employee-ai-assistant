import copy
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


INITIAL_EMPLOYEES: Dict[str, Dict[str, Any]] = {
    "EMP001": {
        "employee_id": "EMP001",
        "name": "Rahul",
        "department": "Engineering",
        "leave_balance": 12,
        "email": "rahul@company.com"
    },
    "EMP002": {
        "employee_id": "EMP002",
        "name": "Priya",
        "department": "HR",
        "leave_balance": 8,
        "email": "priya@company.com"
    }
}


class EmployeeDatabase:
    """In-memory mock database for employee records and submitted leave requests."""

    def __init__(self) -> None:
        self._employees: Dict[str, Dict[str, Any]] = copy.deepcopy(INITIAL_EMPLOYEES)
        self._leave_applications: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def reset(self) -> None:
        with self._lock:
            self._employees = copy.deepcopy(INITIAL_EMPLOYEES)
            self._leave_applications = []

    def get_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        if not employee_id or not isinstance(employee_id, str):
            return None
        cleaned_id = employee_id.strip().upper()
        emp = self._employees.get(cleaned_id)
        return copy.deepcopy(emp) if emp else None

    def update_leave_balance(self, employee_id: str, new_balance: int) -> bool:
        if not employee_id or not isinstance(employee_id, str):
            return False
        cleaned_id = employee_id.strip().upper()
        if cleaned_id in self._employees:
            self._employees[cleaned_id]["leave_balance"] = new_balance
            return True
        return False

    def add_leave_application(self, record: Dict[str, Any]) -> Dict[str, Any]:
        stored_record = copy.deepcopy(record)
        if "created_at" not in stored_record:
            stored_record["created_at"] = datetime.now(timezone.utc).isoformat()
        self._leave_applications.append(stored_record)
        return stored_record
    def commit_leave_application(self, employee_id: str, record: Dict[str, Any], new_balance: int) -> bool:
        """Atomically update balance and append leave record for the in-memory assessment DB."""
        cleaned_id = employee_id.strip().upper()
        with self._lock:
            if cleaned_id not in self._employees:
                return False
            self._employees[cleaned_id]["leave_balance"] = new_balance
            self._leave_applications.append(copy.deepcopy(record))
            return True

    def get_leave_applications(self, employee_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if employee_id:
            cleaned_id = employee_id.strip().upper()
            return [
                copy.deepcopy(app) for app in self._leave_applications
                if app.get("employee_id") == cleaned_id
            ]
        return copy.deepcopy(self._leave_applications)


db = EmployeeDatabase()
