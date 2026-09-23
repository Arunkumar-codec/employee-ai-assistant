# Known Limitations
- Employee data and leave applications are in-memory mock state; process restart resets them.
- Conversation memory is process-local/in-memory and is not suitable for distributed deployment.
- ChromaDB is local persistent storage and must be rebuilt from `documents/` after a clean extraction.
- Employee ID selection is assessment-level identification, not production authentication/authorization.
- Prompt-injection controls are defensive prompting/smoke-test level, not a formal security guarantee.
- Retrieval threshold 1.2 was selected from Phase 7 calibration evidence and should be recalibrated if the corpus/model changes.
