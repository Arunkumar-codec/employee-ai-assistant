# Project State — Phase 7 Candidate

Phase 7 candidate is built from the supplied Phase 6 project, preserving the existing architecture and changing only hardening/finalization areas. The package includes the four-argument public leave tool contract, Rahul/Priya mock data, `conversation_id` context, employee/session isolation, safe DOM rendering, explicit CORS origins, sanitized errors, calibrated RAG defaults (500/50 chunks, top-k 3, threshold 1.2), Gemini transient retry/backoff, fallback source clearing, documentation, and acceptance test definitions.

Static compile and deterministic tests passed in the build environment. Live Gemini/RAG HTTP acceptance must be rerun locally after configuring `.env` and ingesting documents.
