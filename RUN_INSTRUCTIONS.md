# Run Instructions
1. Extract the project and open PowerShell in the project root.
2. Create/activate a Python environment and install `backend/requirements.txt`.
3. Copy `.env.example` to `.env` and set `LLM_API_KEY` (never commit it).
4. Set `$env:PYTHONPATH="backend"`.
5. Build the vector store: `python scripts\ingest_documents.py --rebuild`.
6. Run tests: `python -m pytest backend\tests -v`.
7. Start API: `python -m uvicorn app.main:app --port 8000`.
8. Check `/api/health` and `/docs`.
9. Serve `frontend/` from an allowed origin such as localhost:5500 and run A1-A7 from `docs/ASSESSMENT_TEST_CASES.md`.
