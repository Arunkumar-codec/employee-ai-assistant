# Employee AI Assistant

A FastAPI + RAG + agentic tool-calling assessment project. It answers company-policy questions, retrieves employee information, applies leave, supports multi-tool requests, and maintains conversation context.

## Stack
- FastAPI + Pydantic
- Gemini via `google-genai`
- `sentence-transformers/all-MiniLM-L6-v2` (384-D embeddings)
- ChromaDB vector database
- HTML/CSS/Vanilla JavaScript
- pytest

## Architecture
```text
Company Documents → Chunking (500/50) → Embeddings → ChromaDB

User → Frontend → POST /api/chat → FastAPI
                              ↓
                    Agent / Orchestrator
                   /        |         \
              RAG Search  Employee   Apply Leave
                  ↓         Tool        Tool
              ChromaDB       \          /
                  ↓           Mock Employee DB
            Relevant Context
                  ↓
               Gemini
                  ↓
        Answer + Sources + Tools
                  ↓
               Frontend
```

Detailed architecture: `docs/ARCHITECTURE.md`

## RAG Implementation
Documents are split into **500-character chunks with 50-character overlap**, embedded using `all-MiniLM-L6-v2`, and stored in ChromaDB.

At query time: **Query → Embedding → Chroma Search → Top Chunks → Confidence Filter → Gemini → Answer + Sources**.

Retrieval uses `TOP_K=3` and `RETRIEVAL_SCORE_THRESHOLD=1.2`. Unsupported questions return a no-answer response instead of invented company information.

## Agent Tools
- `search_company_documents(query)` — company-policy RAG search
- `get_employee_info(employee_id)` — employee details and leave balance
- `apply_leave(employee_id, start_date, end_date, reason)` — validates and applies leave

The orchestrator can combine tools for multi-part requests. Conversation context is maintained using an in-memory `conversation_id`.

## Setup (Windows PowerShell)
```powershell
python -m venv .venv-x64
.\.venv-x64\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
# Set LLM_API_KEY in .env
$env:PYTHONPATH="backend"
python scripts\ingest_documents.py --rebuild
cd backend
python -m uvicorn app.main:app --port 8000
```

Frontend (from project root):
```powershell
python -m http.server 5500 --directory frontend
```
Open `http://127.0.0.1:5500`. Full setup: `RUN_INSTRUCTIONS.md`.

## Sample Queries
- `What is the work from home policy?` — RAG
- `Does the company provide pet insurance?` — no-answer prevention
- `How many leaves does EMP001 have?` — tool calling
- `What is the leave policy and how many leaves does EMP001 have?` — multi-tool
- `Apply leave for EMP001 from 2026-10-01 to 2026-10-03 for personal reasons.` — action
- `How many leaves will I have after applying?` — conversation context

## Tests
```powershell
$env:PYTHONPATH="backend"
python -m pytest backend\tests -q
```
**Verified result: 105 passed.** Manual scenarios: `docs/ASSESSMENT_TEST_CASES.md`.

## Assumptions & Limitations
Employee/leave data and conversation state are in-memory and reset on backend restart. The project uses a local company-document knowledge base and does not implement production authentication, persistent HR storage, leave cancellation, or Docker.

## Additional Credit
Implemented: **conversation memory, retrieval confidence threshold, unit tests, and Gemini fallback/reliability handling**.

## Documentation
`RUN_INSTRUCTIONS.md` • `TEST_RESULTS.md` • `docs/ARCHITECTURE.md` • `docs/SAMPLE_QUERIES.md`