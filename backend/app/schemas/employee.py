from typing import Optional
from pydantic import BaseModel, Field


class Employee(BaseModel):
    employee_id: str = Field(..., description="Unique employee identifier (e.g., EMP001)")
    name: str = Field(..., description="Full name of the employee")
    department: str = Field(..., description="Department name")
    leave_balance: int = Field(..., description="Remaining leave days available")
    email: Optional[str] = Field(None, description="Employee corporate email address")


class EmployeeInfoResult(BaseModel):
    found: bool = Field(..., description="Whether the employee was found")
    employee_id: str = Field(..., description="Employee ID queried")
    name: Optional[str] = Field(None, description="Employee name if found")
    department: Optional[str] = Field(None, description="Employee department if found")
    leave_balance: Optional[int] = Field(None, description="Remaining leave balance if found")
    email: Optional[str] = Field(None, description="Employee email if found")
    error: Optional[str] = Field(None, description="Error message if not found or invalid input")


class LeaveApplicationRequest(BaseModel):
    employee_id: str = Field(..., description="Employee ID submitting leave request")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    reason: str = Field(..., description="Reason for leave request")


class LeaveApplicationResult(BaseModel):
    status: str = Field(..., description="Status of the application: 'success' or 'failure'")
    message: str = Field(..., description="Human-readable result or error message")
    application_id: Optional[str] = Field(None, description="Unique Leave Request ID if successful")
    days_requested: Optional[int] = Field(None, description="Calculated duration of leave requested")
    remaining_balance: Optional[int] = Field(None, description="Updated leave balance after deduction")
    employee_id: Optional[str] = Field(None, description="Target employee ID")
