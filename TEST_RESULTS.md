# Final Test Results

## Automated Test Verification

The complete automated test suite was executed from the project root using:

```powershell
$env:PYTHONPATH="backend"
python -m pytest backend\tests -q
```

### Result

**105 passed, 0 failed**

The automated tests cover:

- Document loading and chunking
- Embedding generation
- ChromaDB vector-store operations
- RAG retrieval and grounded responses
- Unsupported-query / hallucination prevention
- Employee information tools
- Leave validation and application
- Agent orchestration
- Multi-tool requests
- Conversation context
- API health
- Gemini fallback and reliability handling
- Application hardening

## Manual Acceptance Tests

End-to-end assessment scenarios are documented in:

`docs/ASSESSMENT_TEST_CASES.md`

The acceptance suite includes:

- A1 — Work-from-home policy (RAG)
- A2 — Annual leave policy (RAG)
- A3 — Unsupported query / hallucination prevention
- A4 — Employee leave-balance tool
- A5 — Multi-tool policy + employee query
- A6 — Leave application
- A7 — Conversational follow-up after leave application

Manual acceptance testing requires a configured Gemini API key, an ingested ChromaDB vector store, and the FastAPI backend running.

The A1-A7 suite should be executed once on the final local package before submission.