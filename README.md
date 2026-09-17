# Employee AI Assistant

RAG + Agentic Employee Assistant — built for an AI Engineering fresher assessment.

## Assessment Objective

Build an Employee AI Assistant that:
- Answers employee questions from company documents using RAG, citing sources.
- Says it can't find an answer rather than hallucinating.
- Performs employee actions (lookup, apply leave) via an agent with tools.

Full requirement breakdown: [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md).
Target architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
Live project state (for resuming work): [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md).

## Current Project Status — Day 1 of 7

| Area | Status |
|---|---|
| Requirements analysis | Implemented |
| Architecture design | Implemented |
| Project structure | Implemented |
| FastAPI app + `/api/health` | Implemented |
| `/api/chat` contract (schemas) | Implemented (returns dev stub, no real AI yet) |
| Frontend chat shell + health check | Implemented |
| Synthetic sample documents | Implemented |
| RAG pipeline (chunking, embeddings, vector DB, retrieval) | Planned — Day 2-3 |
| LLM answer generation | Planned — Day 3 |
| Agent + tools (`search_company_documents`, `get_employee_info`, `apply_leave`) | Planned — Day 4 |
| Conversation memory / follow-ups | Planned — Day 5 |
| Full frontend (sources/tools display polish) | Planned — Day 6 |
| Final docs, diagram, sample queries, packaging | Planned — Day 7 |

## Planned Features

See `docs/REQUIREMENTS.md` sections A–D for the full mandatory list (RAG, the three tools,
multi-tool reasoning, agent actions) and section K for optional bonus items.

## Architecture Overview

```
Documents -> Loader -> Chunking -> Embeddings -> Vector DB -> Retriever -> RAG Service
                                                                              |
Frontend -> POST /api/chat -> Agent -> [KnowledgeSearch | EmployeeInfo | ApplyLeave] -> LLM -> answer+sources+tools_used -> Frontend
```

Full diagram and layer-by-layer responsibilities: `docs/ARCHITECTURE.md`.

## Technology Stack

- **Backend:** Python 3.12+, FastAPI, Uvicorn, Pydantic / pydantic-settings
- **Frontend:** HTML5, CSS3, vanilla JavaScript (no framework/build step)
- **RAG (Day 2+):** ChromaDB, sentence-transformers (local embeddings)
- **LLM (Day 3+):** provider-configurable (e.g. Gemini or equivalent); not hard-coded
- **Testing:** pytest
- **Version control:** Git

## Directory Structure

```
employee-ai-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app entrypoint
│   │   ├── api/routes/        # health.py, chat.py (thin HTTP layer)
│   │   ├── core/config.py     # centralized settings (env-driven)
│   │   ├── schemas/chat.py    # request/response Pydantic models
│   │   ├── services/          # (Day 3+) orchestration
│   │   ├── rag/                # (Day 2+) loader/chunker/embedder/retriever
│   │   ├── agent/              # (Day 4+) tool selection logic
│   │   ├── tools/               # (Day 4+) search/employee-info/apply-leave
│   │   └── data/                # (Day 4+) mock employee DB
│   ├── tests/test_health.py    # Day 1 test suite
│   └── requirements.txt
├── frontend/                    # index.html, css/, js/
├── documents/                   # synthetic demo company documents
├── vector_store/                # ChromaDB persistence (empty on Day 1)
├── docs/                         # REQUIREMENTS.md, ARCHITECTURE.md, PROJECT_STATE.md
├── .env.example
└── pytest.ini
```

## Prerequisites

- Python 3.12+
- pip
- A modern browser (for the frontend)
- Internet access to install Python packages (this repo's Day 1 files were
  authored in a sandbox with no package-install network access — see
  `docs/PROJECT_STATE.md` "Known Issues" for what that means for verification)

## Local Setup

```bash
cd employee-ai-assistant
cp .env.example .env
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
cd backend
pip install -r requirements.txt
```

## Environment Configuration

Copy `.env.example` to `.env` in the project root and adjust values as needed.
No real secrets are committed; `.env` is gitignored. See `.env.example` for
the full list of variables (most LLM/embedding ones are unused until Day 2-3).

## Running Backend

```bash
cd backend
uvicorn app.main:app --reload
```

- Health check: http://localhost:8000/api/health
- Interactive API docs: http://localhost:8000/docs

## Running Frontend

No build step. Serve the `frontend/` folder with any static file server, e.g.:

```bash
cd frontend
python -m http.server 5500
```

Then open http://localhost:5500. It expects the backend at
`http://localhost:8000/api` (edit `API_BASE_URL` in `frontend/js/app.js` if different).

## Running Tests

```bash
# from the project root
pytest
```

## 7-Day Development Roadmap

1. **Day 1 (this state):** requirements, architecture, project scaffold, FastAPI + frontend
   foundations, synthetic documents, Day 1 tests.
2. **Day 2:** document loading, chunking, embeddings, ChromaDB indexing, retriever.
3. **Day 3:** RAG service (context assembly + LLM call), source citation, no-answer handling.
4. **Day 4:** agent + three tools (`search_company_documents`, `get_employee_info`,
   `apply_leave`), multi-tool and action scenarios.
5. **Day 5:** conversation history / follow-up context handling.
6. **Day 6:** frontend polish — sources and tools-used display, loading/error states.
7. **Day 7:** final README/architecture diagram, sample queries, packaging for submission.

## Current Limitations (Day 1)

- `/api/chat` returns a fixed development-stub answer — no RAG, no LLM, no agent yet.
- No embeddings, vector indexing, or retrieval exist yet.
- No employee database or leave-application logic exists yet.
- No conversation memory exists yet.
- Sample documents are synthetic, written for this project, not real company policies.
- Dependencies listed in `backend/requirements.txt` have not been verified to install/run in
  every environment — see `docs/PROJECT_STATE.md` for the exact verification status.
