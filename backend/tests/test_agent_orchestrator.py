from unittest.mock import MagicMock
import pytest

from app.agent.classifier import IntentClassifier, IntentEnum, StructuredIntentOutput, normalize_date_string
from app.agent.orchestrator import AgentOrchestrator
from app.agent.tools_registry import ToolsRegistry


@pytest.fixture
def registry():
    r = MagicMock(spec=ToolsRegistry)
    r.search_company_documents.return_value = {"answer": "Employees get 18 annual leave days.", "sources": ["leave_policy.txt"]}
    r.execute_get_employee_info.side_effect = lambda eid: ({"found": True, "employee_id": "EMP001", "name": "Rahul", "department": "Engineering", "leave_balance": 12, "email": "rahul@company.com"} if eid == "EMP001" else ({"found": True, "employee_id": "EMP002", "name": "Priya", "department": "HR", "leave_balance": 8, "email": "priya@company.com"} if eid == "EMP002" else {"found": False, "employee_id": eid, "error": f"Employee with ID '{eid}' was not found."}))
    r.execute_apply_leave.return_value = {"status": "success", "message": "Leave application submitted successfully.", "remaining_balance": 9}
    return r


def make_agent(registry, output):
    classifier = MagicMock(spec=IntentClassifier)
    classifier.classify.return_value = output
    return AgentOrchestrator(registry, classifier)


def test_01_rag_only(registry):
    a=make_agent(registry, StructuredIntentOutput(intent=IntentEnum.RAG_ONLY)); r=a.process_request("What is the leave policy?")
    assert r.sources == ["leave_policy.txt"] and r.tools_used == ["search_company_documents"]

def test_02_employee_info(registry):
    a=make_agent(registry, StructuredIntentOutput(intent=IntentEnum.EMPLOYEE_INFO, employee_id="EMP001")); r=a.process_request("balance")
    assert "Rahul" in r.answer and "12" in r.answer and r.tools_used == ["get_employee_info"]

def test_03_combined(registry):
    a = make_agent(
        registry,
        StructuredIntentOutput(intent=IntentEnum.RAG_AND_EMPLOYEE_INFO, employee_id="EMP001"),
    )
    message = "What is the leave policy and how many leaves does EMP001 have?"
    r = a.process_request(message)
    registry.search_company_documents.assert_called_once_with("What is the leave policy")
    assert "18 annual" in r.answer and "Rahul" in r.answer
    assert r.tools_used == ["search_company_documents", "get_employee_info"]

def test_04_apply_leave_success(registry):
    o=StructuredIntentOutput(intent=IntentEnum.APPLY_LEAVE,employee_id="EMP001",start_date="2026-09-20",end_date="2026-09-22",reason="travelling"); r=make_agent(registry,o).process_request("apply")
    assert "successfully" in r.answer and "9 days" in r.answer and r.tools_used == ["get_employee_info","apply_leave"]

def test_05_unknown_employee(registry):
    o=StructuredIntentOutput(intent=IntentEnum.EMPLOYEE_INFO,employee_id="EMP999"); r=make_agent(registry,o).process_request("info")
    assert "not found" in r.answer and r.tools_used == ["get_employee_info"]

def test_06_missing_employee(registry):
    o=StructuredIntentOutput(intent=IntentEnum.APPLY_LEAVE,start_date="2026-09-20",end_date="2026-09-22",reason="x"); r=make_agent(registry,o).process_request("apply")
    assert "Employee ID" in r.answer and r.tools_used == []

def test_07_missing_start(registry):
    o=StructuredIntentOutput(intent=IntentEnum.APPLY_LEAVE,employee_id="EMP001",end_date="2026-09-22",reason="x"); r=make_agent(registry,o).process_request("apply")
    assert "start date" in r.answer and r.tools_used == []

def test_08_missing_end(registry):
    o=StructuredIntentOutput(intent=IntentEnum.APPLY_LEAVE,employee_id="EMP001",start_date="2026-09-20",reason="x"); r=make_agent(registry,o).process_request("apply")
    assert "end date" in r.answer and r.tools_used == []

def test_09_missing_reason(registry):
    o=StructuredIntentOutput(intent=IntentEnum.APPLY_LEAVE,employee_id="EMP001",start_date="2026-09-20",end_date="2026-09-22"); r=make_agent(registry,o).process_request("apply")
    assert "reason for leave" in r.answer and r.tools_used == []

def test_10_full_month(): assert normalize_date_string("20 September") == "2026-09-20"
def test_11_abbrev_month(): assert normalize_date_string("20 Sept") == "2026-09-20"
def test_12_invalid_date(): assert normalize_date_string("32 Sept") is None

def test_13_insufficient(registry):
    registry.execute_apply_leave.return_value={"status":"failure","message":"Leave application failed: Insufficient leave balance."}
    o=StructuredIntentOutput(intent=IntentEnum.APPLY_LEAVE,employee_id="EMP001",start_date="2026-01-01",end_date="2026-05-01",reason="vacation"); r=make_agent(registry,o).process_request("apply")
    assert "Insufficient" in r.answer and r.tools_used == ["get_employee_info","apply_leave"]

def test_14_unsupported_rag(registry):
    registry.search_company_documents.return_value={"answer":"I couldn't find this information in the provided documents.","sources":[]}
    r=make_agent(registry,StructuredIntentOutput(intent=IntentEnum.RAG_ONLY)).process_request("space travel")
    assert "couldn't find" in r.answer and r.sources == []

def test_15_exact_tool_accounting(registry):
    r=make_agent(registry,StructuredIntentOutput(intent=IntentEnum.EMPLOYEE_INFO,employee_id="EMP001")).process_request("x")
    assert r.tools_used == ["get_employee_info"]

def test_16_failure_contract(registry):
    registry.execute_apply_leave.return_value={"status":"failure","message":"Insufficient leave balance."}
    o=StructuredIntentOutput(intent=IntentEnum.APPLY_LEAVE,employee_id="EMP001",start_date="2026-09-20",end_date="2026-09-22",reason="x"); r=make_agent(registry,o).process_request("x")
    assert "Leave application failed" in r.answer

def test_17_remaining_balance(registry):
    registry.execute_apply_leave.return_value={"status":"success","message":"Leave application submitted successfully.","remaining_balance":10}
    o=StructuredIntentOutput(intent=IntentEnum.APPLY_LEAVE,employee_id="EMP001",start_date="2026-09-20",end_date="2026-09-22",reason="x"); r=make_agent(registry,o).process_request("x")
    assert "10 days remaining" in r.answer

def test_18_malformed_llm_fallback():
    llm=MagicMock(); llm.generate.return_value="not json"; r=IntentClassifier(llm).classify("What is the leave policy?")
    assert r.intent == IntentEnum.RAG_ONLY

def test_19_unavailable_llm_fallback():
    llm=MagicMock(); llm.generate.side_effect=Exception("offline"); r=IntentClassifier(llm).classify("How many leaves does EMP001 have?")
    assert r.intent == IntentEnum.EMPLOYEE_INFO and r.employee_id == "EMP001"

def test_20_multi_tool_sources(registry):
    o=StructuredIntentOutput(intent=IntentEnum.RAG_AND_EMPLOYEE_INFO,employee_id="EMP002"); r=make_agent(registry,o).process_request("remote work and balance")
    assert r.sources == ["leave_policy.txt"] and r.tools_used == ["search_company_documents","get_employee_info"]
