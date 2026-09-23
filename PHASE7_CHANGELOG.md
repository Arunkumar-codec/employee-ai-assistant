# Phase 7 Changes Applied to the Supplied Phase 6 Base

This package was built by overlaying only Phase 7 hardening/finalization changes on the uploaded Phase 6 project rather than reconstructing the application.

Key changes: calibrated RAG defaults (500/50, top-k 3, threshold 1.2); bounded Gemini transient retry; canonical fallback source clearing; required/normalized employee ID; 404 unknown employee and 403 conversation-owner mismatch; explicit configurable CORS origins; sanitized LLM failure text; four-argument leave contract retained; fallback extraction for `for personal reasons`; timezone-aware timestamps/reset locking; New Conversation frontend control; Phase 7 hardening tests; final architecture/acceptance/interview/run documentation.

The build environment passed compileall and 90 deterministic tests. Real Gemini/vector-store/browser acceptance is intentionally left for the target Windows environment after `.env` configuration and document ingestion.
