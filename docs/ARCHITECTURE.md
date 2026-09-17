# Architecture

## Status

This document describes the **target architecture** for the full 7-day build.
Only the layers marked "Day 1: scaffolded" have actual code today. Everything
else is structural placeholders (`__init__.py` only) to prevent circular
imports later and to make the eventual wiring obvious.

## 1. Ingestion / RAG Pipeline (target, Day 2-3)

```
Company Documents (documents/)
        |
        v
Document Loader          -- reads .txt/.pdf, returns raw text + metadata
        |
        v
Text Cleaning             -- normalize whitespace, strip boilerplate
        |
        v
Chunking                  -- split into overlapping chunks (strategy TBD Day 2)
        |
        v
Embedding Generation       -- local sentence-transformers model (configurable)
        |
        v
Vector Database (ChromaDB, persisted under vector_store/)
        |
        v
Retriever                 -- top-K similarity search + score threshold
        |
        v
RAG Service                -- assembles context + calls LLM, returns answer+sources
```

## 2. Request Lifecycle (target, Day 4-5)

```
User
 |
 v
Frontend (frontend/)
 |
 v
POST /api/chat  { employee_id, message }
 |
 v
Agent (backend/app/agent/)
 |-- decides intent --> Company Knowledge Search tool (RAG)
 |-- decides intent --> Employee Information tool
 |-- decides intent --> Apply Leave tool
 v
LLM / response composition
 |
 v
{ answer, sources[], tools_used[] }
 |
 v
Frontend renders answer, sources, tools used
```

## 3. Layer Responsibilities

| Layer | Path | Responsibility | Day 1 state |
|---|---|---|---|
| Frontend | `frontend/` | Static HTML/CSS/JS chat UI, calls backend over HTTP | Scaffolded — health check + placeholder chat call |
| API routes | `backend/app/api/routes/` | HTTP endpoints only; no business logic | `health.py` implemented, `chat.py` returns dev stub |
| Schemas | `backend/app/schemas/` | Pydantic request/response models (the API contract) | `chat.py` schemas implemented |
| Core / config | `backend/app/core/` | Central settings loading (env vars), app-wide constants | Implemented |
| Services | `backend/app/services/` | Orchestration between agent/RAG and routes | Empty package (Day 3+) |
| RAG | `backend/app/rag/` | Loader, chunker, embedder, vector store client, retriever | Empty package (Day 2) |
| Agent | `backend/app/agent/` | Intent detection, tool selection/orchestration | Empty package (Day 4) |
| Tools | `backend/app/tools/` | `search_company_documents`, `get_employee_info`, `apply_leave` — pure functions, no agent logic | Empty package (Day 4) |
| Data | `backend/app/data/` | Mock employee DB (in-memory/JSON) | Empty package (Day 4) |
| Documents | `documents/` | Synthetic source policy documents for RAG | Implemented (Day 1, synthetic) |
| Vector store | `vector_store/` | ChromaDB persistence directory | Empty dir, created, `.gitkeep` |
| Tests | `backend/tests/` | pytest suite | `test_health.py` implemented |

**Why this separation (interview note):** the assessment explicitly requires RAG logic, agent
logic, and tool implementations to be independently explainable and swappable (e.g., different
LLM/embedding providers). Keeping API routes "thin" and pushing logic into `rag/`, `agent/`,
`tools/`, `services/` means each concern can be unit-tested and modified in isolation, and avoids
circular imports (routes import services; services import rag/agent/tools; rag/agent/tools never
import routes).

## 4. Configuration Layer

`backend/app/core/config.py` uses `pydantic-settings` to load all configuration from environment
variables (`.env`), exposed as a single importable `settings` object. No module reads
`os.getenv()` directly — this keeps configuration centralized and testable, and matches the
assessment's "configuration using environment variables" backend requirement.

**Alternative considered:** plain `os.getenv()` calls scattered through the code. Rejected because
it makes required variables and defaults implicit and harder to test/document.

## 5. Chat API Contract (Day 1)

Request/response shape is fixed today per the assessment (Phase 6). The `/api/chat` route today
returns a clearly-labeled "not implemented yet" response — it does **not** fabricate an AI answer.
This preserves API stability for the frontend and later days while avoiding fake functionality.

## 6. What Is Deliberately Not Built Yet

Embeddings, vector indexing, retrieval, LLM calls, agent tool-selection, employee/leave tool logic,
and conversation memory are all out of scope for Day 1 (see `REQUIREMENTS.md` section N). Building
these prematurely today would violate the 7-day plan and risk producing throwaway/fake code.
