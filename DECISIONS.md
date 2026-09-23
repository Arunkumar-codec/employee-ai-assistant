# ARCHITECTURAL DECISIONS LOG

## Decision 1: FastAPI Backend & Plain Modular Python Tools
Employee tools remain pure standalone Python functions so they are independent of HTTP and LLM SDK layers.

## Decision 2: Single Source of Truth for Employee Data
`backend/app/data/employee_db.py` encapsulates employee state.

## Decision 3: Inclusive Day Calculation for Leave Requests
Formula: `(end_date - start_date).days + 1`.

## Decision 4: In-Memory State Mutability with Reset Standard
State remains in memory for the assessment and `reset()` provides deterministic unit tests.
