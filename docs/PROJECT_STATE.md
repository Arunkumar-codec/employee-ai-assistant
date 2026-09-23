# Project State

## Project
RAG + Agentic Employee Assistant

## Current Day
Day 2 of 7 — COMPLETE (STATICALLY VERIFIED). Runtime verification (real `pytest` run, real
embedding model, real Chroma index, real Gemini call) is REQUIRED LOCALLY — see "Local
Verification Required" below. Day 1 baseline remains RUNTIME VERIFIED (see Day 1 section).

## Assessment Source
`AI_Engineering_Assessment.pdf` (attached to the original request). Full requirement
breakdown lives in `docs/REQUIREMENTS.md`; do not re-derive requirements from memory —
read that file first in any new conversation.

---

## Day 1 Baseline (preserved, unchanged)

- **Status:** COMPLETE AND LOCALLY VERIFIED (RUNTIME VERIFIED on Windows, Python 3.12.10).
- `pytest 8.3.4`: 6 tests collected, 6 passed, 0 failed at the time.
- `GET /api/health` → HTTP 200. `POST /api/chat` → HTTP 200 with the Day-1 stub.
- Windows note: direct `uvicorn.exe` execution is blocked by Windows Application Control.
  Working command: `python -m uvicorn app.main:app --reload`. This is an environment
  restriction, not a project-code issue — do not attempt to "fix" it.
- Full historical detail (frontend verification, exact commands) is unchanged from the
  original Day-1 record and is not repeated here — see git history / the Day-1 ZIP if needed.

---

## Day 2 Completed

### RAG pipeline (`backend/app/rag/`)
- `loader.py` — loads `.txt` (and `.pdf`, via `pypdf`, registered but untested against a real
  PDF — no PDF exists in the current corpus), conservative whitespace normalization, retains
  source filename / document_type / page metadata.
- `chunker.py` — 700-char chunks, 120-char overlap, natural-boundary splitting (paragraph →
  sentence → space → hard cut), stable deterministic IDs (`{source}::{index:04d}` or
  `{source}::p{page}::{index:04d}`), no empty chunks, tiny trailing fragments merged into the
  previous chunk. Reasoning documented in the module docstring and README.
- `embedder.py` — `sentence-transformers/all-MiniLM-L6-v2`, lazy-loaded once, cached via
  `lru_cache`. Dimension (384) read from the model at runtime, not hard-coded.
- `vector_store.py` — ChromaDB `PersistentClient`, collection created with
  `hnsw:space="cosine"` (explicit — Chroma's default is squared-L2, wrong for this model).
  Dedup via deterministic IDs + `upsert()`. `rebuild_collection()` for full re-index.
- `retriever.py` — `search_company_documents(query, top_k=None)`, configurable top-k
  (`settings.top_k`, default 4).
- `context_builder.py` — `[Source: ...]` labeled context blocks for the LLM.
- `prompts.py` — strict grounding system prompt, exact no-answer sentence, basic
  prompt-injection instruction (ignore instruction-like text inside retrieved content).

### Services (`backend/app/services/`)
- `llm_service.py` — `LLMProvider` interface + `GeminiProvider` (current `google-genai` SDK,
  not the deprecated `google-generativeai`). Lazy client creation — a missing `LLM_API_KEY`
  never crashes the app at import/startup.
- `rag_service.py` — `answer_question(question)`: validate → retrieve → threshold check
  (smaller cosine distance = more relevant, `<=` comparison) → no-answer short-circuit →
  context → LLM call → dedup sources (order-preserving). LLM failure returns a clear
  "unavailable" message with empty sources, never a fabricated answer.

### API
- `backend/app/api/routes/chat.py` — replaced the Day-1 stub with a call to
  `rag_service.answer_question`; same request/response schema (unchanged since Day 1); a
  final `try/except` safety net logs unexpected exceptions internally and returns a generic
  message rather than leaking exception details to the frontend.
- `backend/app/main.py` — title/description/version strings updated to reflect Day 2; CORS
  and router registration unchanged.

### Configuration (`backend/app/core/config.py`)
- Added: `documents_directory`, `embedding_model`, `chroma_persist_directory`,
  `chroma_collection_name`, `chunk_size` (700), `chunk_overlap` (120), `llm_provider`
  (default `gemini`), `llm_model` (default `gemini-2.5-flash`). `top_k` (4) and
  `retrieval_score_threshold` (now 0.8, was placeholder 0.0) were already scaffolded, now used.
- `PROJECT_ROOT` computed from `config.py`'s own file location so `documents_directory` and
  `chroma_persist_directory` resolve correctly regardless of the process's working directory
  (uvicorn from `backend/` vs. pytest/scripts from the project root).

### Scripts (`scripts/`, new top-level directory)
- `ingest_documents.py` — the one ingestion workflow: load → chunk → embed → upsert. Reports
  document/chunk counts, embedding dimension, collection name, persistence path. `--rebuild`
  flag for a full clean re-index. Not run automatically at FastAPI startup, per the assessment.
- `inspect_retrieval.py` — diagnostic: runs the five required manual questions through real
  retrieval and prints best distance + would-answer/would-no-answer verdict per question, to
  support local threshold calibration (see "Known Issues" below).

### Dependencies (`backend/requirements.txt`)
- Added: `chromadb==0.5.23` (pre-1.0, deliberately avoiding CVE-2026-45829 which affects the
  1.0.0-1.5.9 HTTP-server mode — not applicable to this project's embedded `PersistentClient`
  usage either way, but avoided outright), `sentence-transformers==3.3.1`, `pypdf==5.1.0`,
  `google-genai>=1.0.0` (left as a minimum bound, not an exact pin — this sandbox has no
  network access to verify PyPI's current exact release; see the requirements.txt comment for
  how to pin it exactly once installed locally). No LangChain/LlamaIndex added — see README
  "Why no framework?".

### Configuration files
- `.env.example` — added `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY` (real Day-2 use, was
  Day-3+ placeholder), `CHROMA_COLLECTION_NAME`, updated `RETRIEVAL_SCORE_THRESHOLD` default,
  commented-out `DOCUMENTS_DIRECTORY`/`CHROMA_PERSIST_DIRECTORY` (now default to absolute
  paths computed from code location — see config.py note above). No real secrets added.
- `.gitignore` — already correctly protected `vector_store/*` (except `.gitkeep`); unchanged.

### Documentation
- `README.md` — Day 2 status table, updated architecture diagram (with real module names),
  "Why no framework?" note, full RAG design section (ingestion, chunking strategy + reasoning,
  embedding model + dimensionality, vector database + dedup strategy, retrieval approach,
  no-answer/confidence strategy + calibration procedure, RAG prompt/grounding, LLM provider),
  updated directory structure, Windows-specific setup/run commands, ingestion + diagnostic
  script usage, manual RAG test procedure, updated roadmap, Day-2 known limitations.
- `docs/ARCHITECTURE.md` — Day-2 pipeline diagram with real file/function names replacing the
  Day-1 "target" placeholder diagram, updated layer-responsibility table, new "Distance
  Semantics" section (cosine, smaller-is-better, `<=` comparison — explicitly called out
  because getting this backwards silently inverts the no-answer logic), updated "what's not
  built yet" section for Day 3+ scope.
- `docs/REQUIREMENTS.md` — statuses updated for all Day-2-relevant rows (RAG requirements,
  `search_company_documents`, retrieval confidence threshold, prompt injection protection) to
  COMPLETED, with a footnote on sandbox verification status; new PROJECT DESIGN DECISION
  entries for the Gemini choice, no-framework choice, chunking numbers, and threshold
  calibration approach; out-of-scope section updated to Day-2 boundary.
- `docs/INTERVIEW_NOTES.md` — created. 20 beginner-friendly WHAT/WHY/HOW/ALTERNATIVE
  explanations covering RAG, chunking, overlap, embeddings, vectors, semantic similarity,
  vector databases, ChromaDB, ingestion, retrieval, top-k, distance semantics, thresholds,
  hallucination, source-from-metadata, local embeddings, embedding/LLM separation, and what
  would change at production scale.

### Tests (`backend/tests/`)
46 test functions across 8 files (up from 6 tests in 1 file on Day 1):
- `test_health.py` (5 tests, was 6) — the Day-1 chat-stub-specific test was **replaced** with a
  comment explaining why (the stub no longer exists; its coverage moved to `test_chat_rag.py`
  with more thorough Day-2 behavior tests). All other Day-1 tests (app import, config load,
  health status/body, 404) preserved verbatim.
- `test_loader.py` (7 tests) — txt loading, metadata, directory-level loading, missing/empty
  directory errors, unsupported-extension skipping, whitespace normalization, empty-file error.
- `test_chunker.py` (7 tests) — single-chunk short docs, multi-chunk long docs with no empty
  chunks, stable/unique chunk IDs, page-number IDs, overlap presence, chunk_size>overlap
  validation, multi-document flattening. **Also manually run directly against the real
  `documents/*.txt` corpus in this sandbox (not via pytest, since pytest itself isn't
  installed here)** — see "Tests Actually Executed" below.
- `test_embedder.py` (6 tests) — batch embedding, empty input, empty-query rejection,
  dimension pass-through, singleton caching, load-failure propagation. All via a fake model
  (monkeypatched), no real sentence-transformers needed.
- `test_vector_store.py` (7 tests) — cosine-space collection creation, upsert (not add),
  no-duplicate-on-repeat-id, mismatched-length validation, empty-collection query, shaped
  query result, rebuild-clears-data. All via a fake Chroma client (monkeypatched).
- `test_retriever.py` (3 tests) — blank-query short-circuit, result shaping, top_k
  pass-through. Via fake embedder/vector-store (monkeypatched).
- `test_rag_service.py` (6 tests) — empty question, relevant-question grounded answer,
  no-chunks no-answer, beyond-threshold no-answer, LLM-failure handling (no fake sources),
  source deduplication. Via fake retrieval/LLM (monkeypatched) — this is the test module that
  most directly exercises the required "pet insurance" hallucination-prevention behavior.
- `test_chat_rag.py` (5 tests) — route response shape, no-answer response shape, missing
  required fields → 422, exception safety net (no leaked exception details). Via
  `TestClient` + monkeypatched `answer_question`.

---

## Files Created (Day 2)

```
backend/app/rag/loader.py
backend/app/rag/chunker.py
backend/app/rag/embedder.py
backend/app/rag/vector_store.py
backend/app/rag/retriever.py
backend/app/rag/context_builder.py
backend/app/rag/prompts.py
backend/app/services/llm_service.py
backend/app/services/rag_service.py
scripts/ingest_documents.py
scripts/inspect_retrieval.py
backend/tests/test_loader.py
backend/tests/test_chunker.py
backend/tests/test_embedder.py
backend/tests/test_vector_store.py
backend/tests/test_retriever.py
backend/tests/test_rag_service.py
backend/tests/test_chat_rag.py
docs/INTERVIEW_NOTES.md
```

## Files Modified (Day 2)

```
backend/app/core/config.py       (new Day-2 settings, PROJECT_ROOT-based absolute paths)
backend/app/api/routes/chat.py   (real RAG answers instead of the Day-1 stub)
backend/app/main.py              (title/description/version strings only)
backend/tests/test_health.py     (chat-stub test replaced with an explanatory comment)
backend/requirements.txt         (chromadb, sentence-transformers, pypdf, google-genai added)
.env.example                     (Day-2 LLM/embedding/retrieval/chunking variables)
README.md                        (Day-2 status, RAG design section, setup/run instructions)
docs/ARCHITECTURE.md             (Day-2 pipeline diagram, layer table, distance semantics)
docs/REQUIREMENTS.md             (Day-2 statuses, new design-decision entries)
```

## Dependencies Added

`chromadb==0.5.23`, `sentence-transformers==3.3.1`, `pypdf==5.1.0`, `google-genai>=1.0.0` — see
`backend/requirements.txt` for the reasoning behind each pin/bound.

## RAG Architecture

See `docs/ARCHITECTURE.md` section 1 for the full implemented pipeline diagram and section 6
for distance semantics. Summary: `loader → chunker → embedder → vector_store` runs offline via
`scripts/ingest_documents.py`; `retriever → context_builder → prompts → llm_service` runs
per-request inside `rag_service.answer_question`, called from `POST /api/chat`.

## Document Loading

TXT (implemented, used by the current corpus) and PDF (implemented via `pypdf`, registered,
but **not exercised against a real PDF** since none exists in `documents/` — flagged as a known
gap, not silently assumed to work).

## Chunking Strategy

700-character chunks, 120-character overlap, chosen by inspecting the actual structure of the
six synthetic documents (not picked blindly from the assessment's suggested range). Full
reasoning: `backend/app/rag/chunker.py` docstring and README "Chunking Strategy". Sanity-run
directly against the real `documents/*.txt` files in this sandbox (see "Tests Actually
Executed") — 6 documents in, 12 chunks out, zero empty chunks, all chunk IDs unique.

## Embedding Model

`sentence-transformers/all-MiniLM-L6-v2`, local, 384-dimension (read from model, not assumed),
cosine similarity. Reasoning: README "Embedding Model" / `embedder.py` docstring.

## Vector Database

ChromaDB `PersistentClient`, `hnsw:space="cosine"` explicit, deterministic-ID upsert for
deduplication, `rebuild_collection()` for full re-index. Reasoning: README "Vector Database" /
`vector_store.py` docstring.

## Retrieval Strategy

`search_company_documents(query, top_k=None)`, `TOP_K` configurable (default 4, env
`TOP_K`). Reasoning: `retriever.py` docstring.

## Confidence / Threshold Strategy

Cosine distance, smaller = more relevant, `RETRIEVAL_SCORE_THRESHOLD` default **0.8**,
`<=` comparison against the best (smallest) retrieved distance. **This default value is a
documented starting point only — NOT verified against the real embedding model**, because this
sandbox has no network access to download `all-MiniLM-L6-v2` (see "Known Issues"). Calibrate
locally with `python scripts/inspect_retrieval.py` before trusting it, per README.

## LLM Provider

Google Gemini via `google-genai` (current SDK; `google-generativeai` is deprecated and was
deliberately not used). Behind `LLMProvider` interface in `llm_service.py`. Lazy client
creation — missing `LLM_API_KEY` degrades gracefully (`/api/health` still works; `/api/chat`
returns a clear unavailable message) rather than crashing at import.

## Environment Variables

See `.env.example` for the full current list with inline explanations. New in Day 2:
`LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `CHROMA_COLLECTION_NAME`,
`RETRIEVAL_SCORE_THRESHOLD` (now used), `EMBEDDING_MODEL` (now used), optionally
`DOCUMENTS_DIRECTORY` / `CHROMA_PERSIST_DIRECTORY` / `CHUNK_SIZE` / `CHUNK_OVERLAP` (commented
out, defaulting to code-computed absolute paths / the documented 700/120 values).

## Tests

**46 test functions across 8 files** (see "Day 2 Completed > Tests" above for the full
breakdown by file). Every RAG/service/route test mocks its external dependency
(chromadb, sentence-transformers, or the Gemini client) — no test requires network access, a
real API key, or a pre-built vector index.

### Tests Actually Executed

**pytest itself is NOT installed in this authoring sandbox** (no network access — confirmed:
`pip install pytest` fails with "No matching distribution found"). The full `pytest` suite has
**NOT been run** here. What WAS actually done in this sandbox:

- `python3 -m py_compile` on every `.py` file under `backend/` and `scripts/` — **all pass**
  (STATICALLY VERIFIED: no syntax errors, no truncated files from any interruption).
- The real `loader.py` + `chunker.py` were imported and run directly (not via pytest, no mocks)
  against the actual `documents/*.txt` files: 6 documents loaded, 12 chunks produced, all
  non-empty, all chunk IDs unique. **RUNTIME VERIFIED**, but only for loader+chunker — these two
  modules need no external dependency (chromadb/sentence-transformers/google-genai) to run.
- `app/services/rag_service.answer_question` was run directly (with `pydantic_settings`,
  `search_company_documents`, and the LLM client all stubbed/mocked by hand in this sandbox,
  since none of `pydantic-settings`, `chromadb`, `sentence-transformers`, or `google-genai` are
  installed here) for three cases: a relevant question (grounded answer + correct source), the
  pet-insurance question (correct no-answer response, empty sources), and a blank question
  (clarifying message, no search performed). **All three produced the expected result.** This is
  RUNTIME VERIFIED for `rag_service`'s branching logic specifically, using hand-built stubs —
  it is NOT a substitute for the real `pytest` suite (which exercises more edge cases per
  module) or for a real end-to-end run with the actual embedding model, Chroma index, and
  Gemini API.
- Embedder, vector store, retriever, and the chat route were reviewed by static code inspection
  and cross-checked for import/interface consistency (settings field names, function
  signatures, schema shapes) but were **NOT executed** in this sandbox beyond the py_compile
  check, since exercising them meaningfully needs the real packages.

**Distinguishing STATICALLY VERIFIED vs. RUNTIME VERIFIED, precisely:**
- STATICALLY VERIFIED (this sandbox): all `.py` files compile; all settings/imports/schemas are
  cross-consistent (manually reviewed); the 46 pytest test functions are written and believed
  correct but their `assert`s have not all actually been executed by pytest.
- RUNTIME VERIFIED (this sandbox): `loader.py` + `chunker.py` against real documents;
  `rag_service.py`'s branching logic against hand-built stubs.
- **NOT YET VERIFIED ANYWHERE:** the real `pytest` suite has never been run (not in this
  sandbox, not yet on your machine); no real embedding has ever been computed by the real
  model; no real Chroma index has ever been built; no real Gemini API call has ever been made;
  the FastAPI app has never actually been started with real dependencies installed.

## Manual Verification

Not performed anywhere yet (requires your local machine — see "Local Verification Required").

## Known Issues

1. **pytest suite unexecuted** — see "Tests Actually Executed" above. Run it locally before
   trusting the 46 test functions to actually pass; they were written carefully and checked for
   syntax/consistency, but an unrun test can still contain a mistaken assertion.
2. **`RETRIEVAL_SCORE_THRESHOLD` default (0.8) is uncalibrated** — chosen as a reasonable
   starting point for cosine distance on a small policy-document corpus, but never checked
   against the real `all-MiniLM-L6-v2` model's actual output distances (no network access in
   this sandbox to download the model). Run `python scripts/inspect_retrieval.py` locally and
   adjust `RETRIEVAL_SCORE_THRESHOLD` in `.env` if any of the five required questions gives the
   wrong verdict.
3. **PDF loading untested against a real PDF** — `load_pdf_document` is implemented and
   registered but the current `documents/` corpus is TXT-only, so it has never actually run.
4. **`google-genai` version left as `>=1.0.0`, not pinned exactly** — no network access here to
   check PyPI's current exact release. Pin it exactly in `backend/requirements.txt` once
   installed locally, per the comment there.
5. **No real Gemini API call has ever been made** — `GeminiProvider` was reviewed by inspection
   against the `google-genai` SDK's documented usage pattern (`genai.Client(api_key=...)`,
   `client.models.generate_content(model=..., contents=..., config=types.GenerateContentConfig(system_instruction=...))`)
   but has never actually been executed, mocked or otherwise, against the real SDK's types —
   only `LLMProviderError` handling around it was exercised (via a fake provider class, not the
   real `GeminiProvider` class itself).

## Design Decisions

- **PROJECT DESIGN DECISION:** no LangChain/LlamaIndex — plain Python + chromadb +
  sentence-transformers throughout, so every step is directly explainable in the interview.
- **PROJECT DESIGN DECISION:** Gemini chosen as the Day-2 LLM provider (free developer tier),
  behind a provider interface so it's not a hard dependency of the RAG service itself.
- **PROJECT DESIGN DECISION:** deterministic chunk IDs + upsert (not full-rebuild-every-time)
  for deduplication — cheaper on repeated ingestion, with `--rebuild` available for the
  document-deletion edge case upsert alone can't handle.
- **PROJECT DESIGN DECISION:** `chromadb==0.5.23` pinned pre-1.0 specifically to sidestep
  CVE-2026-45829 (a 1.0.0-1.5.9 HTTP-server-mode vulnerability) outright, even though this
  project's embedded `PersistentClient` usage isn't exposed to that attack surface either way.
- **PROJECT DESIGN DECISION:** no-answer behavior implemented generically via distance
  threshold + strict prompt — no hard-coded "pet insurance" (or any other) keyword check
  anywhere in the RAG/service logic (verified by inspection: `grep -rn "pet insurance"
  backend/app` returns no matches; the phrase appears only as a test question string in
  `scripts/inspect_retrieval.py`, never in a conditional).

## Interview Notes

See `docs/INTERVIEW_NOTES.md` — 20 WHAT/WHY/HOW/ALTERNATIVE explanations covering the full Day-2
concept list (RAG, chunking, overlap, embeddings, vectors, semantic similarity, vector
databases, ChromaDB, ingestion, retrieval, top-k, distance semantics, thresholds, hallucination,
source-from-metadata, local embeddings, embedding/LLM separation, production-scale changes).

## Next Day Plan (Day 3 → really "Day 4" per the assessment's own Part 2/3, per the Day-2 master
prompt's explicit scope boundary — the Day-2 prompt skips ahead to agent/tools as "Day 4"):

1. Run local verification first (see "Local Verification Required") — do not start Day 4 work
   on an unverified Day-2 base.
2. Implement `backend/app/data/` — mock employee DB (EMP001/Rahul, EMP002/Priya, etc.).
3. Implement `backend/app/tools/` — `get_employee_info(employee_id)`, `apply_leave(...)`.
4. Implement `backend/app/agent/` — intent detection / tool selection, reusing
   `app/rag/retriever.py:search_company_documents` as-is (not duplicated) for the RAG tool.
5. Wire the agent into `/api/chat`, still preserving the exact same response schema.
6. Add agent/tool tests, mocking the LLM and the mock DB as needed.
7. Update `docs/REQUIREMENTS.md` sections C/D statuses and this file at the end.

## Local Verification Required: YES

Run these from the project root, in order, on your Windows machine:

```powershell
# 1. activate the existing .venv
.venv\Scripts\activate

# 2. install Day-2 dependencies (adds to the already-verified Day-1 set)
cd backend
pip install -r requirements.txt
cd ..

# 3. configure environment
copy .env.example .env
# then edit .env and set LLM_API_KEY to a real Gemini key from
# https://aistudio.google.com/apikey

# 4. build the vector index (required before any RAG question works)
python scripts/ingest_documents.py

# 5. run the full test suite
pytest

# 6. calibrate the no-answer threshold against your real corpus
python scripts/inspect_retrieval.py
# if any question shows the wrong verdict, adjust RETRIEVAL_SCORE_THRESHOLD in .env and re-run

# 7. run the backend (note: python -m uvicorn, not a bare uvicorn.exe — see Day-1 Windows note)
cd backend
python -m uvicorn app.main:app --reload

# 8. in another terminal, test the five required questions, e.g.:
#    (or use http://localhost:8000/docs interactively)
curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" ^
  -d "{\"employee_id\": \"EMP001\", \"message\": \"What is the work from home policy?\"}"
curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" ^
  -d "{\"employee_id\": \"EMP001\", \"message\": \"Does the company provide pet insurance?\"}"

# 9. run the frontend (separate terminal, from the project root)
cd frontend
python -m http.server 5500
# open http://localhost:5500 and try the same questions through the UI
```

Record the actual pytest pass/fail counts and any threshold adjustment you make back into this
file (or a fresh continuation prompt) before starting Day 4.

## Last Verified State

- **Day 1 Status:** COMPLETE AND LOCALLY VERIFIED (RUNTIME VERIFIED, preserved from before).
- **Day 2 Status:** COMPLETE (STATICALLY VERIFIED) — code review, py_compile, cross-file
  consistency checks, and hand-stubbed logic runs of `loader`/`chunker`/`rag_service` all pass
  in this sandbox. The real `pytest` suite, the real embedding model, the real Chroma index,
  and the real Gemini API have **never been run** — that is Day 2's required next action on
  your machine, not a remaining implementation gap.
- **Day 3/4 Readiness:** READY, contingent on completing local verification first.
