# Requirements Mapping

Source of truth: `AI_Engineering_Assessment.pdf` (attached assessment document).
Anything not traceable to that document is explicitly labeled **PROJECT DESIGN DECISION**.

Status values: `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `BLOCKED`

---

## A. Mandatory Requirements

| Requirement | Mandatory | Day | Status |
|---|---|---|---|
| Answer employee questions from company documents (RAG) | Yes | 2 | COMPLETED* |
| Mention source document(s) for each answer | Yes | 2 | COMPLETED* |
| Respond "I couldn't find this information in the provided documents." when unavailable | Yes | 2 | COMPLETED* |
| Perform employee actions via agent + tools | Yes | 4 | NOT_STARTED |
| Working backend | Yes | 1-5 | IN_PROGRESS |
| Working frontend | Yes | 1,6 | IN_PROGRESS |

\* Implemented and statically reviewed; not yet confirmed with a live `pytest` run or a real
Gemini call in the authoring sandbox (no network access there) — see `docs/PROJECT_STATE.md` for
exact verification status and local commands to confirm.

## B. RAG Requirements

| Requirement | Mandatory | Day | Status |
|---|---|---|---|
| Document loading | Yes | 2 | COMPLETED |
| Document chunking | Yes | 2 | COMPLETED |
| Embedding generation | Yes | 2 | COMPLETED |
| Store embeddings in vector DB | Yes | 2 | COMPLETED |
| Retrieve relevant chunks | Yes | 2 | COMPLETED |
| Pass retrieved context to LLM | Yes | 2 | COMPLETED |
| Return answer + sources | Yes | 2 | COMPLETED |

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
| Company Knowledge Search | `search_company_documents(query)` | Yes | 2 (implemented), 4 (wired to agent) | COMPLETED (Day 2 part) |
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
| RAG pipeline | Yes | 2 | COMPLETED* |
| Agent implementation | Yes | 4 | NOT_STARTED |
| Tool calling | Yes | 4 | NOT_STARTED |
| Error handling | Yes | 1 (baseline), 2 (RAG errors), ongoing | IN_PROGRESS |
| Configuration via environment variables | Yes | 1-2 | COMPLETED |

\* See footnote under section A re: sandbox verification status.

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
| `POST /chat` request shape `{employee_id, message}` | Yes | 1 (contract), 2 (RAG logic), 4-5 (tools/memory) | IN_PROGRESS |
| Response shape `{answer, sources, tools_used}` | Yes | 1 (contract), 2 (RAG logic), 4-5 (tools/memory) | IN_PROGRESS |

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
| "What is the work from home policy?" | RAG retrieval | 2 | IMPLEMENTED, local verification pending |
| "How many annual leaves are allowed?" | RAG retrieval | 2 | IMPLEMENTED, local verification pending |
| "Does the company provide pet insurance?" | Hallucination prevention | 2 | IMPLEMENTED, local verification pending |
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
| Retrieval confidence threshold | 2 | COMPLETED* (threshold value needs local calibration — see README) |
| Docker setup | 7 (stretch) | NOT_STARTED |
| Unit tests | 1,2 (ongoing) | IN_PROGRESS |
| Logging/Observability | ongoing | IN_PROGRESS (basic: chat route logs unexpected exceptions) |
| Prompt injection protection | 2 | COMPLETED (system-prompt level: retrieved-content instructions ignored) |
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
- PROJECT DESIGN DECISION: LLM provider is left configurable (not hard-coded to any vendor); Day 2
  ships a Gemini implementation behind that interface, chosen for its free developer tier.
- PROJECT DESIGN DECISION: no LangChain/LlamaIndex — the RAG pipeline is plain Python + chromadb +
  sentence-transformers, so every step is directly explainable in the assessment interview (see
  README "Why no framework?").
- PROJECT DESIGN DECISION: chunk size (700) and overlap (120) were chosen by inspecting the actual
  structure of the six synthetic documents, not picked arbitrarily from the assessment's suggested
  range — see README "Chunking Strategy" for the reasoning.
- PROJECT DESIGN DECISION: `RETRIEVAL_SCORE_THRESHOLD` default (0.8) is a documented starting
  point only — the assessment itself says threshold calibration depends on the actual corpus, and
  this sandbox has no network access to download the real embedding model and verify it. A
  diagnostic script (`scripts/inspect_retrieval.py`) is provided for local calibration instead of
  pretending a guessed number is verified.

## N. Out-of-Scope Items (Day 2)

Agent tool-selection logic, `get_employee_info`, `apply_leave`, the mock employee database,
multi-tool reasoning, action-request handling, conversation memory, reranking, Docker,
authentication, deployment, elaborate UI — all deferred per the Day 2 scope rule (see the Day-2
master prompt's explicit exclusion list).
