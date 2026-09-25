# Run and Test Instructions

These commands are the supported way to run the submitted project on Windows PowerShell.

## 1. Prerequisites

Install 64-bit Python 3.11, 3.12, or 3.13 and Git. Python must be available as `python`.

Verify:

```powershell
python --version
python -c "import platform,sys; print(sys.version); print(platform.machine())"
```

On Windows ARM64, use an x64/AMD64 Python environment under Windows emulation if `torch` cannot be installed. The project needs PyTorch through `sentence-transformers`.

## 2. Open the project root

```powershell
cd <path-to-extracted-project>
```

The directory must contain `backend`, `frontend`, `documents`, `scripts`, and `.env.example`.

## 3. Create and activate the virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
```

If PowerShell blocks activation, run this once in that terminal and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

## 4. Configure environment variables

```powershell
Copy-Item .env.example .env
notepad .env
```

Set at least:

```text
LLM_API_KEY=<primary Gemini API key>
```

Optional quota/rate-limit failover:

```text
LLM_FALLBACK_API_KEY=<secondary Gemini API key>
```

Never commit or submit the real `.env` file.

## 5. Build the vector index

Run from the project root:

```powershell
python scripts\ingest_documents.py --rebuild
```

This downloads/loads the embedding model on first use and rebuilds `vector_store` from the supplied `documents` directory.

## 6. Run the automated tests

Run from the project root:

```powershell
python -m pytest -q
```

Verified package result: `105 passed`.

Do not run the suite from inside `backend`; some tests intentionally import through the project-root package path.

## 7. Start the backend

Open PowerShell in the project root, activate the same environment, then:

```powershell
.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Keep this terminal open.

Check:

- API health: `http://127.0.0.1:8000/api/health`
- Swagger UI: `http://127.0.0.1:8000/docs`

## 8. Start the frontend

Open a second PowerShell terminal at the project root:

```powershell
.venv\Scripts\Activate.ps1
python -m http.server 5500 --directory frontend
```

Open `http://127.0.0.1:5500` in a browser.

Do not open `frontend/index.html` directly with `file://`; serve it through the HTTP command above so CORS behavior matches the configured application.

## 9. Quick acceptance checks

Use employee `EMP001` and try:

```text
What is the leave policy?
How many leaves do I have?
What insurance benefits are provided by the company?
What is the leave policy and how many leaves do I have?
```

For leave actions, use future dates and provide a reason. Past start dates are rejected. If a prompt states a number of leave days that conflicts with its date range, the assistant asks for correction instead of applying the leave.

For the complete acceptance set, use `docs/ASSESSMENT_TEST_CASES.md`.

## 10. Troubleshooting

### `ModuleNotFoundError: No module named 'backend'` while testing

Return to the project root and run:

```powershell
python -m pytest -q
```

### `No matching distribution found for torch`

This commonly occurs with a native Windows ARM Python environment. Install/use an x64 Python interpreter and recreate `.venv`, then reinstall `backend\requirements.txt`.

### Backend starts but RAG gives no useful answers

Rebuild the index:

```powershell
python scripts\ingest_documents.py --rebuild
```

Confirm the `documents` directory contains the supplied company text files.

### Gemini quota/rate-limit error

Configure `LLM_FALLBACK_API_KEY` in `.env`. The application switches to the secondary key for transient Gemini capacity/quota failures. If both credentials are unavailable or exhausted, it returns a controlled service-unavailable response.

### Frontend says backend is unreachable

Confirm the backend terminal is still running and open `http://127.0.0.1:8000/api/health`. The default frontend server must use port `5500`.
