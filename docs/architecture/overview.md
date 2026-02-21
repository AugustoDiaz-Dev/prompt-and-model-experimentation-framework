# Architecture Overview — Prompt and Model Experimentation Framework

> **Project 3** · `project-3/framework/`

## System Overview

The Experimentation Framework allows prompt engineers and developers to test combinations of models, prompts, and hyper-parameters against a structured dataset. It logs metrics, evaluates hallucination rates, integrates with MLflow for long-term tracking, and runs A/B test analysis to make data-driven prompt release decisions.

```
                 ┌──────────────────┐
   Register      │                  │  POST /prompts
  ──────────────▶│   FastAPI API    │──────────────────────────▶  PromptRegistry
                 │   (async)        │                                     │
   Run Exp       │                  │  POST /experiments                  │
  ──────────────▶│                  │──────────────────────────▶  ExperimentRunner
                 │                  │                                     │
   A/B Test      │                  │  POST /ab-tests                     │
  ──────────────▶└──────────────────┘                                     │
                                                                          ▼
                                                              ┌───────────────────────┐
                                                              │  PostgreSQL            │
                                                              │  prompts               │
                                                              │  experiments           │
                                                              │  metrics               │
                                                              │  ab_tests              │
                                                              └───────────────────────┘
                                                                          ▼
                                                                  MLflow server
```

---

## Core Modules

### 1) Prompt Registry
- Handles versionings, metadata (tags), and authors.
- `compare(v1, v2)`: Returns character diff, semantic similarity, and token-level deltas.

### 2) Experiment Runner
- Compiles prompt templates + evaluation dataset.
- Simulates/executes API calls to LLMs (OpenAI, local).
- Gathers accuracy, cost, latency, and passes outputs to Hallucination Detector.
- Logs run details automatically to MLflow.

### 3) Metrics & Hallucination Scoring
- Computes standard deviations and 95% Confidence Intervals.
- **HallucinationDetector**: Offline rule-based scanning for unsupported absolutes, ungrounded numbers, and self-contradictory logic.

### 4) A/B Testing Engine
- Non-parametric comparison of historical experiments (Mann-Whitney U).
- Calculates Cohen's `d` for effect sizes.
- Simulates traffic routing.

### 5) Report Generator
- Generates reproducible, portable Markdown and HTML reports covering metric summaries, configuration deltas, and statistical significance analysis.
