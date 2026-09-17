# Project State

## Project
RAG + Agentic Employee Assistant

## Current Day
Day 1 of 7 — COMPLETE AND LOCALLY VERIFIED. Day 1 runtime-verification blocker: RESOLVED. Day 2 readiness: READY.

## Assessment Source
`AI_Engineering_Assessment.pdf` (attached to the original request). Full requirement
breakdown lives in `docs/REQUIREMENTS.md`; do not re-derive requirements from memory —
read that file first in any new conversation.

## Completed

- Requirements analysis: `docs/REQUIREMENTS.md` (sections A–N, all assessment requirements
  mapped with mandatory/optional, planned day, status).
- Architecture design: `docs/ARCHITECTURE.md` (ingestion pipeline, request lifecycle, layer
  responsibilities, config approach).
- Project directory structure created exactly as planned (see README "Directory Structure").
- `backend/app/core/config.py` — centralized `pydantic-settings` config, loads from `.env`.
- `backend/app/schemas/chat.py` — `ChatRequest` / `ChatResponse` Pydantic models matching the
  assessment's JSON contract.
- `backend/app/api/routes/health.py` — `GET /api/health`.
- `backend/app/api/routes/chat.py` — `POST /api/chat`, returns an explicit "not implemented
  yet" stub using the real response schema. No fabricated AI answers.
- `backend/app/main.py` — FastAPI app, CORS configured from `settings.frontend_origin`,
  routers registered under `/api`.
- `backend/tests/test_health.py` — 6 tests: app import, config load, health status code,
  health body shape, 404 on invalid route, chat stub shape/content.
- `frontend/index.html`, `frontend/css/styles.css`, `frontend/js/app.js` — chat shell with
  employee-ID input, message list, sources/tools-used meta display, loading state, error
  banner, and a live `/api/health` check on load. Talks to backend via `fetch`.
- `documents/*.txt` — 6 synthetic company documents (leave, WFH, travel, benefits,
  IT/security, FAQ), clearly labeled as synthetic, deliberately excluding any pet-insurance
  content (reserved for later hallucination-prevention testing).
- `.env.example`, `.gitignore`, `pytest.ini`, `backend/requirements.txt`.
- `README.md` — full Day 1 status, setup, roadmap, limitations.
- Git repository initialized, one commit made, working tree clean, no secrets committed.

## Partially Completed

- `POST /api/chat` exists and matches the contract, but only returns a static stub — no RAG,
  no LLM, no agent behind it yet (by design, per Day 1 scope rules).

## Not Started

- RAG pipeline: document loading/chunking/embeddings/vector store/retrieval (`app/rag/` is an
  empty package — Day 2).
- LLM-backed answer generation and source citation (Day 3).
- Agent + tools: `search_company_documents`, `get_employee_info`, `apply_leave`
  (`app/agent/`, `app/tools/`, `app/data/` are empty packages — Day 4).
- Conversation memory / follow-up resolution (Day 5).
- Frontend polish beyond the Day 1 shell (Day 6).
- Architecture diagram image, final README, 5+ sample queries writeup, submission packaging
  (Day 7). A text-based diagram already exists in `docs/ARCHITECTURE.md` and `README.md`.

## Current Architecture

See `docs/ARCHITECTURE.md` for the full diagram and layer table. Summary: routes stay thin;
`services/` will orchestrate `rag/`, `agent/`, `tools/`; `agent/` will never be imported by
`rag/` or `tools/` (one-directional dependency to avoid circular imports).

## Important Files

- `backend/app/main.py` — app entrypoint, router registration, CORS.
- `backend/app/core/config.py` — all configuration; never call `os.getenv()` elsewhere.
- `backend/app/schemas/chat.py` — the API contract; keep stable across days.
- `backend/app/api/routes/chat.py` — replace the stub body with real
  agent/RAG orchestration starting Day 3-4; keep the response schema unchanged.
- `documents/*.txt` — source data for Day 2 ingestion.
- `docs/REQUIREMENTS.md` — update the `status` column as each requirement is implemented.

## Dependencies

Pinned in `backend/requirements.txt` (Day 1 set only — fastapi, uvicorn, pydantic,
pydantic-settings, python-dotenv, pytest, httpx). ChromaDB, sentence-transformers, and an
LLM client are intentionally **not yet added** — add them at the start of Day 2/3 respectively.

## Configuration

`.env.example` documents every variable currently planned (app metadata, API host/port,
frontend origin/CORS, LLM provider/model/key, embedding model, Chroma persist directory,
top_k, retrieval score threshold). `.env` itself is gitignored and does not exist in this
repo — no secrets were ever created or committed.

## Commands

```bash
# setup
cd employee-ai-assistant
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
cd backend && pip install -r requirements.txt

# run backend
python -m uvicorn app.main:app --reload   # from backend/ (or: uvicorn app.main:app --reload)

# run frontend
python -m http.server 5500      # from frontend/

# run tests
pytest                          # from project root
```

## Tests

6 tests written in `backend/tests/test_health.py`, covering: app import, config load, health
endpoint status + body shape, invalid-route 404, and chat-stub shape/content (asserts the
answer says "not implemented" and sources/tools_used are empty, i.e. asserts we are NOT
faking an AI answer).

**Execution status: EXECUTED AND VERIFIED.**
- Framework: `pytest 8.3.4`
- Environment: Python 3.12.10 on Windows (`.venv`)
- Results: 6 tests collected, 6 passed, 0 failed
- Warnings: 1 non-blocking Starlette/AnyIO `DeprecationWarning`
- All 6 unit tests pass cleanly against the live local environment.

## Known Issues

1. **Verification blocker: RESOLVED.**
   - Day 1 dependencies installed successfully in `.venv` (Python 3.12.10, Windows).
   - Automated tests: 6 passed out of 6.
   - Backend runtime note: Direct `uvicorn` executable was blocked by Windows Application Control. This is an environment restriction, not a project-code failure. Working command: `python -m uvicorn app.main:app --reload`.
2. Day 1 pinned dependency versions installed cleanly on Python 3.12.10 (Windows). Day 2 dependencies (`chromadb`, `sentence-transformers`) will be installed and verified at Day 2 kickoff.

## Important Design Decisions

- **PROJECT DESIGN DECISION:** `/chat` from the assessment is implemented as `/api/chat` for
  consistency with `/api/health`. Functionally identical to what the assessment asked for.
- **PROJECT DESIGN DECISION:** synthetic documents were authored for this project (no real
  company documents were provided) and are clearly labeled as synthetic in each file.
- **PROJECT DESIGN DECISION:** employee/leave data will be an in-memory mock (matching the
  assessment's own example), not a relational database.
- **PROJECT DESIGN DECISION:** LLM provider is left unconfigured/pluggable on Day 1; no vendor
  chosen yet, no API calls made yet.

## Assessment Requirements Mapping

Full mapping lives in `docs/REQUIREMENTS.md` — treat that file, not this section, as the
source of truth for per-requirement status.

## Next Day Plan (Day 2)

1. Add `chromadb` and an embedding library (e.g. `sentence-transformers`) to
   `backend/requirements.txt` — verify install with real network access first.
2. Implement `backend/app/rag/loader.py` (reads `documents/*.txt`).
3. Implement `backend/app/rag/chunker.py` — decide and document a chunking strategy
   (e.g. fixed-size with overlap) with a WHAT/WHY/HOW/alternatives note in `ARCHITECTURE.md`.
4. Implement `backend/app/rag/embedder.py` and `backend/app/rag/vector_store.py` (Chroma,
   persisted to `vector_store/`).
5. Implement `backend/app/rag/retriever.py` (top-K + score threshold from `settings`).
6. Write unit tests for each of the above in isolation before wiring into `/api/chat`.
7. Update `docs/REQUIREMENTS.md` statuses and this file at the end of Day 2.

## Last Verified State

- **Day 1 Status:** COMPLETE AND LOCALLY VERIFIED
- **Day 1 Runtime-Verification Blocker:** RESOLVED
- **Day 2 Readiness:** READY

### Environment
- OS: Windows
- Python: 3.12.10
- Virtual environment: `.venv`
- Day 1 dependencies installed successfully.

### Automated Tests
- `pytest 8.3.4`
- 6 tests collected
- 6 passed
- 0 failed
- 1 non-blocking Starlette/AnyIO `DeprecationWarning`

### Backend Runtime
- Direct `uvicorn` executable was blocked by Windows Application Control.
- This is an environment restriction, not a project-code failure.
- Working command: `python -m uvicorn app.main:app --reload` (from `backend/`)
- Verified:
  - FastAPI application starts successfully.
  - `GET /api/health` returns HTTP 200.
  - Response: `{"status":"ok","service":"Employee AI Assistant"}`
  - Swagger UI `/docs` loads successfully (along with `/openapi.json`).
  - `POST /api/chat` returns HTTP 200.
  - Chat endpoint correctly returns the Day 1 development stub.
  - No fake RAG answer is generated.

### Frontend
- Served successfully using: `python -m http.server 5500` (from `frontend/`)
- Frontend loaded at `http://127.0.0.1:5500`
- Frontend health check successfully detected backend.
- UI displayed: `Backend: connected (Employee AI Assistant)`
- EMP001 message successfully reached `POST /api/chat`.
- Stub response rendered correctly.
- Sources displayed as none.
- Tools used displayed as none.
