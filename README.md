# Employee AI Assistant

A FastAPI + RAG + agentic tool-calling assessment project. It answers company-policy questions from supplied documents, reports employee information, combines policy retrieval with employee data, applies leave, and preserves bounded conversation context.

## Stack
- FastAPI + Pydantic
- Gemini via `google-genai`
- `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional embeddings)
- ChromaDB persistent local vector store
- HTML/CSS/Vanilla JavaScript frontend
- pytest


## Architecture

```text
Employee / User
      |
      v
Frontend UI (HTML + CSS + JavaScript)
      |
      |  POST /api/chat
      v
FastAPI Backend
      |
      v
Agent / Orchestrator + Intent Detection
      |
      +----> RAG Search ----> Chroma Vector DB
      |                         |
      |                         v
      |                   Relevant Documents
      |                         |
      |                         v
      |                     Gemini LLM
      |
      +----> Employee Tool ----> Mock Employee DB
      |
      +----> Leave Tool -------> Mock Employee DB
      |
      v
Answer + Sources + Tools Used
      |
      v
Frontend UI
```
## Assessment tools
- `search_company_documents(query)`
- `get_employee_info(employee_id)`
- `apply_leave(employee_id, start_date, end_date, reason)` — requested days are calculated inclusively by the server.

Mock employees: EMP001 Rahul / Engineering / 12 leave days; EMP002 Priya / HR / 8 leave days. State is in-memory and resets when the process restarts.

## Setup (Windows PowerShell)
```powershell
cd <project-root>
python -m venv .venv-x64
.\.venv-x64\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
# Edit .env and set LLM_API_KEY. LLM_FALLBACK_API_KEY is optional.
$env:PYTHONPATH="backend"
python scripts\ingest_documents.py --rebuild
python -m uvicorn app.main:app --port 8000
```
Do not commit `.env`. If direct `uvicorn.exe` is blocked on Windows, use `python -m uvicorn` as above.

Open Swagger at `http://127.0.0.1:8000/docs`. The static frontend is in `frontend/`; serve it from an origin listed in `CORS_ORIGINS` (default includes localhost:5500).

## API
`POST /api/chat`
```json
{"employee_id":"EMP001","message":"What is the leave policy?","conversation_id":null}
```
`conversation_id` is optional for a new conversation. Reuse the returned value for follow-ups. Changing employees must start a new conversation.

## Tests
```powershell
$env:PYTHONPATH="backend"
python -m pytest backend\tests -v
```
The current package build passed 98 deterministic tests in the build environment. Re-run them on the target Windows environment before submission, then run the live A1-A7 acceptance suite in `docs/ASSESSMENT_TEST_CASES.md` with a configured Gemini key and ingested vector store.

## Security and reliability
The project keeps secrets in environment configuration, uses explicit configurable CORS origins, sanitizes unexpected HTTP errors, validates requests, isolates conversations by employee, renders dynamic frontend text with safe DOM APIs, supports a secondary Gemini API key for transient quota/capacity failover with bounded retries, and prevents follow-up balance checks from replaying leave actions. These are assessment-level controls, not a claim of production-grade authentication/security.
