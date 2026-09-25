import pytest
from backend.app.data.employee_db import db
from backend.app.tools.employee_tools import get_employee_info, apply_leave


@pytest.fixture(autouse=True)
def reset_database():
    db.reset()
    yield


def test_get_employee_info_emp001():
    res = get_employee_info("EMP001")
    assert res["found"] is True
    assert res["name"] == "Rahul"
    assert res["department"] == "Engineering"
    assert res["leave_balance"] == 12


def test_get_employee_info_emp002():
    res = get_employee_info("emp002")
    assert res["found"] is True
    assert res["name"] == "Priya"
    assert res["department"] == "HR"
    assert res["leave_balance"] == 8


def test_get_employee_info_unknown():
    res = get_employee_info("EMP999")
    assert res["found"] is False
    assert "error" in res


def test_get_employee_info_invalid_input():
    res = get_employee_info("")
    assert res["found"] is False


def test_apply_leave_success():
    res = apply_leave("EMP001", "2026-10-20", "2026-10-22", "Vacation travel")
    assert res["status"] == "success"
    assert res["days_requested"] == 3
    assert res["remaining_balance"] == 9
    emp = get_employee_info("EMP001")
    assert emp["leave_balance"] == 9


def test_apply_leave_unknown_employee():
    res = apply_leave("EMP999", "2026-10-20", "2026-10-22", "Vacation")
    assert res["status"] == "failure"
    assert "not found" in res["message"]


def test_apply_leave_invalid_dates():
    res = apply_leave("EMP001", "2026-13-01", "2026-10-22", "Vacation")
    assert res["status"] == "failure"
    assert "Invalid date format" in res["message"]


def test_apply_leave_end_before_start():
    res = apply_leave("EMP001", "2026-10-22", "2026-10-20", "Vacation")
    assert res["status"] == "failure"
    assert "cannot be earlier" in res["message"]


def test_apply_leave_insufficient_balance():
    res = apply_leave("EMP001", "2026-10-01", "2026-10-15", "Long trip")
    assert res["status"] == "failure"
    assert "Insufficient leave balance" in res["message"]
    emp = get_employee_info("EMP001")
    assert emp["leave_balance"] == 12


def test_apply_leave_empty_reason():
    res = apply_leave("EMP001", "2026-10-20", "2026-10-22", "   ")
    assert res["status"] == "failure"
    assert "reason must be provided" in res["message"]


def test_leave_applications_recording():
    res = apply_leave("EMP002", "2026-10-01", "2026-10-02", "Conference")
    assert res["status"] == "success"
    apps = db.get_leave_applications("EMP002")
    assert len(apps) == 1
    assert apps[0]["days_requested"] == 2
    assert apps[0]["reason"] == "Conference"


def test_multiple_leave_applications_sequential_deduction():
    res1 = apply_leave("EMP001", "2026-10-01", "2026-10-02", "Trip 1")
    assert res1["status"] == "success"
    assert res1["remaining_balance"] == 10
    res2 = apply_leave("EMP001", "2026-10-10", "2026-10-12", "Trip 2")
    assert res2["status"] == "success"
    assert res2["remaining_balance"] == 7
    emp = get_employee_info("EMP001")
    assert emp["leave_balance"] == 7


def test_apply_leave_rejects_past_start_date():
    res = apply_leave("EMP001", "2025-09-25", "2025-09-30", "Old request")
    assert res["status"] == "failure"
    assert "cannot be in the past" in res["message"]
    assert get_employee_info("EMP001")["leave_balance"] == 12
