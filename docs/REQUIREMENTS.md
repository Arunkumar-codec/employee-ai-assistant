# Requirements Mapping

Source of truth: `AI_Engineering_Assessment.pdf` (attached assessment document).
Anything not traceable to that document is explicitly labeled **PROJECT DESIGN DECISION**.

Status values: `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `BLOCKED`

---

## A. Mandatory Requirements

| Requirement | Mandatory | Day | Status |
|---|---|---|---|
| Answer employee questions from company documents (RAG) | Yes | 2-3 | NOT_STARTED |
| Mention source document(s) for each answer | Yes | 2-3 | NOT_STARTED |
| Respond "I couldn't find this information in the provided documents." when unavailable | Yes | 3 | NOT_STARTED |
| Perform employee actions via agent + tools | Yes | 4 | NOT_STARTED |
| Working backend | Yes | 1-5 | IN_PROGRESS |
| Working frontend | Yes | 1,6 | IN_PROGRESS |

## B. RAG Requirements

| Requirement | Mandatory | Day | Status |
|---|---|---|---|
| Document loading | Yes | 2 | NOT_STARTED |
| Document chunking | Yes | 2 | NOT_STARTED |
| Embedding generation | Yes | 2 | NOT_STARTED |
| Store embeddings in vector DB | Yes | 2 | NOT_STARTED |
| Retrieve relevant chunks | Yes | 2 | NOT_STARTED |
| Pass retrieved context to LLM | Yes | 3 | NOT_STARTED |
| Return answer + sources | Yes | 3 | NOT_STARTED |

## C. Agent Requirements

| Requirement | Mandatory | Day | Status |
|---|---|---|---|
| Agent decides which tool(s) to call based on intent | Yes | 4 | NOT_STARTED |
| Scenario 1: RAG only | Yes | 4 | NOT_STARTED |
| Scenario 2: Tool only (employee info) | Yes | 4 | NOT_STARTED |
| Scenario 3: Multiple tools combined | Yes | 4 | NOT_STARTED |
| Scenario 4: Action request (apply leave) | Yes | 4 | NOT_STARTED |

## D. Required Tools

| Tool | Function Signature | Mandatory | Day | Status |
|---|---|---|---|---|
| Company Knowledge Search | `search_company_documents(query)` | Yes | 2 (scaffold), 4 (wired to agent) | NOT_STARTED |
| Employee Information | `get_employee_info(employee_id)` | Yes | 4 | NOT_STARTED |
| Apply Leave | `apply_leave(employee_id, start_date, end_date, reason)` | Yes | 4 | NOT_STARTED |

Mock employee DB (EMP001/Rahul, EMP002/Priya, etc.) — Mandatory, Day 4, NOT_STARTED.

## E. Conversational-Context Requirements

| Requirement | Mandatory | Day | Status |
|---|---|---|---|
| Maintain basic conversation history | Yes | 5 | NOT_STARTED |
| Follow-up question resolves to prior topic (e.g. "leave" reference) | Yes | 5 | NOT_STARTED |

## F. Backend Requirements

| Requirement | Mandatory | Day | Status |
|---|---|---|---|
| API endpoints | Yes | 1-5 | IN_PROGRESS |
| RAG pipeline | Yes | 2-3 | NOT_STARTED |
| Agent implementation | Yes | 4 | NOT_STARTED |
| Tool calling | Yes | 4 | NOT_STARTED |
| Error handling | Yes | 1 (baseline), ongoing | IN_PROGRESS |
| Configuration via environment variables | Yes | 1 | COMPLETED |

## G. Frontend Requirements

| Requirement | Mandatory | Day | Status |
|---|---|---|---|
| Ask questions | Yes | 1 (foundation), 6 (full) | IN_PROGRESS |
| View assistant responses | Yes | 1 (foundation), 6 | IN_PROGRESS |
| View document sources | Yes | 6 | NOT_STARTED |
| See tool usage | Optional (recommended) | 6 | NOT_STARTED |

## H. Required API Behavior

| Requirement | Mandatory | Day | Status |
|---|---|---|---|
| `POST /chat` request shape `{employee_id, message}` | Yes | 1 (contract), 3-5 (real logic) | IN_PROGRESS |
| Response shape `{answer, sources, tools_used}` | Yes | 1 (contract), 3-5 (real logic) | IN_PROGRESS |

> PROJECT DESIGN DECISION: assessment shows path as `/chat`. We are namespacing
> it as `/api/chat` for consistency with `/api/health`. Documented, not hidden.

## I. Submission Deliverables

| Deliverable | Mandatory | Day | Status |
|---|---|---|---|
| Source code (GitHub/ZIP) | Yes | 7 | NOT_STARTED |
| Working frontend | Yes | 6-7 | IN_PROGRESS |
| Working backend | Yes | 5-7 | IN_PROGRESS |
| README (setup, architecture, tech, chunking, embeddings, vector DB, retrieval, agent/tools, assumptions, limitations) | Yes | 1 (initial), 7 (final) | IN_PROGRESS |
| Architecture diagram | Yes | 1 (initial), 7 (final) | IN_PROGRESS |
| 5+ sample queries (RAG, no-answer, tool usage, multi-tool, leave application) | Yes | 7 | NOT_STARTED |

## J. Required Sample/Test Scenarios

| Query | Expected Capability | Day | Status |
|---|---|---|---|
| "What is the work from home policy?" | RAG retrieval | 2-3 | NOT_STARTED |
| "How many annual leaves are allowed?" | RAG retrieval | 2-3 | NOT_STARTED |
| "Does the company provide pet insurance?" | Hallucination prevention | 3 | NOT_STARTED |
| "How many leaves does EMP001 have?" | Tool calling | 4 | NOT_STARTED |
| "What is the leave policy and how many leaves does EMP001 have?" | Multi-tool reasoning | 4 | NOT_STARTED |
| "Apply leave for EMP001 from 20 Sept to 22 Sept." | Agent action | 4 | NOT_STARTED |
| "How many leaves will I have after applying?" | Conversational context | 5 | NOT_STARTED |

## K. Bonus Requirements (Optional)

| Item | Day (if attempted) | Status |
|---|---|---|
| Streaming responses | 7 (stretch) | NOT_STARTED |
| Conversation memory | 5 (core memory is mandatory; this overlaps) | NOT_STARTED |
| Metadata filtering | 7 (stretch) | NOT_STARTED |
| Reranking | 7 (stretch) | NOT_STARTED |
| Retrieval confidence threshold | 3 | NOT_STARTED |
| Docker setup | 7 (stretch) | NOT_STARTED |
| Unit tests | 1,7 (ongoing) | IN_PROGRESS |
| Logging/Observability | ongoing | NOT_STARTED |
| Prompt injection protection | 7 (stretch) | NOT_STARTED |
| Basic authorization for employee actions | 7 (stretch) | NOT_STARTED |

## L. Interview Expectations

Must be able to explain: RAG pipeline, chunking strategy rationale, embeddings/retrieval mechanics,
agent tool-selection logic, frontend↔backend communication, and all design decisions/assumptions/limitations.
This drives the "WHAT/WHY/HOW/alternatives" documentation convention used throughout `docs/`.

## M. Assumptions

- PROJECT DESIGN DECISION: No real company documents were provided alongside the assessment, so
  synthetic demo documents are created for development/testing (Phase 8).
- PROJECT DESIGN DECISION: Employee/leave data is in-memory/mocked; no relational database is introduced
  since the assessment only asks for a mock employee database.
- PROJECT DESIGN DECISION: LLM provider is left configurable (not hard-coded to any vendor); Day 1 ships
  no LLM calls at all.

## N. Out-of-Scope Items (Day 1)

Production RAG, embeddings, Chroma indexing, final retrieval, LLM answer generation, agent tool
selection, employee-information tool logic, leave application logic, complex conversation memory,
reranking, Docker, authentication, deployment, elaborate UI — all deferred per the Day 1 scope rule.
