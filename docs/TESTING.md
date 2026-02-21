# How to test the project

You can verify the framework in two ways: **unit tests** (no services required) and **API smoke test** (requires Docker + running API).

---

## 1. Unit tests (fast, no Docker)

Runs all pytest tests. They use mocks and do not need Postgres or MLflow.

```bash
# From the repo root (after cloning)
source .venv/bin/activate   # macOS/Linux, after: python -m venv .venv

# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```

**Expected:** All tests pass (e.g. 9 passed). If any fail, the project is not in a good state.

---

## 2. Full stack + API smoke test

This checks that the API and database work end-to-end.

### Step 1: Start infrastructure

```bash
# From the repo root
docker compose up -d
```

Wait until both `framework-postgres-1` and `framework-mlflow-1` are **Up** (`docker ps`).

### Step 2: Start the API

In a **separate terminal**:

```bash
# From the repo root
source .venv/bin/activate
# Or ensure .env exists (copy from .env.example)
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Leave it running. You should see “Application startup complete” and “Uvicorn running on http://127.0.0.1:8000”.

### Step 3: Run the smoke script

In **another terminal**:

```bash
# From the repo root
./scripts/smoke_test.sh
```

Or manually:

- **Health:** `curl -s http://127.0.0.1:8000/health` → `{"status":"ok"}`
- **Register a prompt:**  
  `curl -s -X POST http://127.0.0.1:8000/prompts -H "Content-Type: application/json" -d '{"name":"smoke","content":"You are helpful.","author":"tester"}'`
- **List prompts:** `curl -s http://127.0.0.1:8000/prompts`
- **Run experiment:**  
  `curl -s -X POST http://127.0.0.1:8000/experiments -H "Content-Type: application/json" -d '{"name":"smoke-exp","prompt_content":"Say hello.","model_name":"gpt-3.5-turbo","test_cases":[{"input":"Hi","expected":"Hello"}]}'`

If all return HTTP 200 (and experiments return JSON with `id`, `accuracy`, etc.), the project is working.

### Step 4: Optional – interactive API docs

Open in the browser:

- **API docs:** http://127.0.0.1:8000/docs  
- **MLflow UI:** http://127.0.0.1:5001  

---

## Summary

| What you want           | Command / action                                      |
|-------------------------|--------------------------------------------------------|
| Quick check (no deps)   | `pytest tests/ -v`                                    |
| Check with coverage     | `pytest tests/ -v --cov=app --cov-report=term-missing`|
| Full stack works        | `docker compose up -d` → run API → `./scripts/smoke_test.sh` |
| Try API by hand         | http://127.0.0.1:8000/docs                            |
