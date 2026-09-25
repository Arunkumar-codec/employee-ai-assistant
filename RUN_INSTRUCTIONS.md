# Run and Test Instructions

## 1. Prerequisites

Install **64-bit Python 3.11–3.13** and Git.

> Windows ARM64 users should use x64/AMD64 Python if PyTorch installation fails.

## 2. Setup

Open PowerShell in the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

## 3. Configure Gemini

```powershell
Copy-Item .env.example .env
notepad .env
```

Set the Gemini API key in `.env`:

```text
LLM_API_KEY=<your Gemini API key>
```

`LLM_FALLBACK_API_KEY` is optional. Never commit the real `.env` file.

## 4. Build Vector Index

From the project root:

```powershell
python scripts\ingest_documents.py --rebuild
```

This indexes the supplied company documents using the configured embedding model and ChromaDB.

## 5. Run Tests

```powershell
python -m pytest -q
```

Verified result: **105 passed**.

## 6. Start Backend

```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Swagger API documentation:

`http://127.0.0.1:8000/docs`

## 7. Start Frontend

Open a second PowerShell terminal from the project root:

```powershell
.venv\Scripts\Activate.ps1
python -m http.server 5500 --directory frontend
```

Open:

`http://127.0.0.1:5500`

## 8. Quick Test

Use employee ID `EMP001` and try:

```text
What is the leave policy?
How many leaves do I have?
What insurance benefits are provided by the company?
What is the leave policy and how many leaves do I have?
```

For leave applications, use future dates and include a reason.

See `docs/ASSESSMENT_TEST_CASES.md` for the complete acceptance tests.

## Troubleshooting

- **RAG not returning expected answers:** Run `python scripts\ingest_documents.py --rebuild`.
- **PyTorch installation fails on Windows ARM64:** Use an x64/AMD64 Python environment.
- **Gemini quota exhausted:** Configure `LLM_FALLBACK_API_KEY` in `.env`.
- **Frontend cannot connect:** Confirm the backend is running on port `8000` and the frontend on port `5500`.