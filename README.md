# Prompt and Model Experimentation Framework (Project 3)

This folder contains the **boilerplate + first working steps** for **Project 3: Prompt and Model Experimentation Framework** from `project.md`.

## What you can do now

- Register prompts with versioning and metadata
- Run experiments with different prompts/models/configurations
- Track metrics (accuracy, latency, cost)
- Perform A/B testing with statistical comparison
- Generate experiment reports

## Requirements

- Python **3.11+**
- Docker (for Postgres and MLflow)

## Quickstart

Clone the repo and from its root:

```bash
git clone https://github.com/AugustoDiaz-Dev/prompt-and-model-experimentation-framework.git
cd prompt-and-model-experimentation-framework
docker compose up -d
```

Create a virtualenv and install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,mlflow]"
```

Run the API:

```bash
export DATABASE_URL="postgresql+asyncpg://experiments:experiments@localhost:5434/experiments"
export MLFLOW_TRACKING_URI="http://localhost:5001"
uvicorn app.main:app --reload --port 8002
```

## API

- `GET /health`
- `POST /prompts` (register a prompt)
- `GET /prompts` (list prompts)
- `POST /experiments` (run an experiment)
- `GET /experiments/{id}` (get experiment results)
- `POST /ab-tests` (run A/B test)
- `GET /reports/{experiment_id}` (generate report)

## Testing

- **Unit tests (no Docker):** `pytest tests/ -v`
- **Full check:** See [docs/TESTING.md](docs/TESTING.md) for unit tests, coverage, and API smoke test with Docker + running API.

## Tracking

Use [docs/TESTING.md](docs/TESTING.md) to verify the project. Copy `.env.example` to `.env` and set `DATABASE_URL` and optionally `MLFLOW_TRACKING_URI` and `OPENAI_API_KEY`.
