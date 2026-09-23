# Requirements Traceability
| Requirement | Implementation | Evidence/Status |
|---|---|---|
| Company documents | `documents/` six supplied/synthetic policy files | Implemented |
| Loading/chunking | `app/rag/loader.py`, `chunker.py` | Implemented |
| Embeddings | `app/rag/embedder.py` MiniLM 384d | Implemented |
| Vector DB/retrieval | `vector_store.py`, `retriever.py` Chroma cosine | Implemented |
| Context + grounded LLM | `context_builder.py`, `prompts.py`, `rag_service.py`, `llm_service.py` | Implemented; live local retest required |
| Sources | retrieval metadata in `rag_service.py` | Implemented |
| Unsupported fallback | canonical no-answer + source clearing | Implemented |
| search_company_documents | RAG service/registry | Implemented |
| get_employee_info | `tools/employee_tools.py` | Deterministically tested |
| apply_leave 4-arg contract | `tools/employee_tools.py` | Deterministically tested |
| Mock employees | `data/employee_db.py` Rahul/Priya | Deterministically tested |
| RAG/tool/multi-tool/action | `agent/orchestrator.py` | Deterministically tested; live local A1-A7 pending |
| Conversation follow-up/isolation | `services/session_service.py` | Deterministically tested |
| FastAPI backend | `app/main.py`, `api/routes/` | Implemented |
| Functional frontend | `frontend/` | Implemented; browser retest locally |
| Tests/docs/architecture/samples | `backend/tests/`, `docs/`, root guides | Included |
