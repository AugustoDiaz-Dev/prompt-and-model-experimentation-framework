## Project 3: Prompt and Model Experimentation Framework — Status

This file tracks what's been implemented in `framework/` and what remains from **Project 3** in `project.md`.

### ✅ Achieved (boilerplate + first steps)

- **Service scaffold**: FastAPI app (`app/main.py`)
- **Config + logging**: env-driven settings + JSON logging (`app/core/`)
- **Database**: async SQLAlchemy engine/session (`app/db/session.py`)
- **Data models**: `prompts`, `experiments`, `metrics`, `ab_tests` tables (`app/db/models.py`)
- **Prompt Registry**: version control, metadata tagging, comparison (`app/registry/prompt_registry.py`)
- **Experiment Runner**: model selection, temperature, max_tokens, seed control (`app/experiment/experiment_runner.py`)
- **Metrics Module**: accuracy, latency, cost tracking with confidence intervals (`app/metrics/metrics.py`)
- **A/B Testing Module**: statistical comparison using scipy, significance calculation (`app/ab_testing/ab_testing.py`)
- **MLflow Integration**: basic tracker interface (`app/mlflow_integration/mlflow_tracker.py`)
- **Report Generator**: markdown report generation (`app/reporting/report_generator.py`)
- **API endpoints**:
  - `GET /health`
  - `POST /prompts` (register prompt)
  - `GET /prompts` (list prompts)
  - `POST /experiments` (run experiment)
  - `GET /experiments/{id}` (get experiment results)
  - `POST /ab-tests` (run A/B test)
  - `GET /reports/{experiment_id}` (generate report)
- **Initial tests**: metrics calculation tests (`tests/test_metrics.py`)
- **Local infra**: `docker-compose.yml` for Postgres + MLflow

### ⏳ Remaining (from Project 3 scope)

#### 1) Prompt Registry
- [x] Version control
- [x] Metadata tagging
- [x] Prompt comparison
- [x] **Enhanced comparison** (diff visualization, semantic similarity, characters/tokens)

#### 2) Experiment Runner
- [x] Model selection
- [x] Temperature control
- [x] Context window configuration (max_tokens)
- [x] Deterministic seed control
- [x] **Real LLM integration** (replace mock with actual API calls)
- [x] **Multiple model providers** (OpenAI, Anthropic, local models)

#### 3) Metrics Module
- [x] Accuracy tracking
- [x] Latency tracking
- [x] Cost per call tracking
- [x] Confidence intervals
- [x] **Hallucination rate detection** (rule-based heuristics, no API needed)
- [x] **Additional metrics** (token usage, response quality scores)

#### 4) A/B Testing Module
- [x] Traffic split simulation
- [x] Statistical comparison using scipy
- [x] Significance calculation
- [x] Decision logging
- [x] **Advanced statistical tests** (using Mann-Whitney U for robustness)
- [x] **Multiple metric comparison** (effect size - Cohen's d added)

#### 5) MLflow Integration
- [x] Basic tracker interface
- [x] **Full integration**: track parameters, metrics directly from ExperimentRunner
- [x] **Run comparison** in MLflow UI
- [x] **Artifact storage** (prompts, outputs, reports)

#### 6) Benchmark Dataset
- [x] **Benchmark dataset**: added `datasets/experiments/benchmark.json` (categories + context)
- [x] **Dataset loader** for experiments

#### 7) Report Generator
- [x] Basic experiment report (markdown)
- [x] Basic A/B test report (markdown)
- [x] **Enhanced reports** (charts, visualizations)
- [x] **Export formats** (added HTML generation)
- [x] **Automated report generation** (scheduled, on-demand)
