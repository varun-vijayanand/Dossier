# Dossier

**An AI investigation assistant for anti-money-laundering (AML) alerts.** Dossier gathers evidence for each transaction-monitoring alert through an MCP server, grounds its reasoning in public typology guidance using RAG, and drafts a cited, India-STR-style investigation narrative. A human reviews and approves every outcome. Nothing is closed, escalated, or filed automatically.

> **Status: early development.** The data foundation is being built. The architecture below is the design, and the roadmap shows what exists today. No evaluation results have been measured yet, and none are claimed.

## Why

Transaction-monitoring systems raise far more alerts than analysts can work, and most are false positives. Every investigation repeats the same steps: read the alert, pull the customer profile, scan transactions, check counterparties, compare against known patterns, and write it up. That is slow, inconsistent between analysts, and hard to audit.

Fluent but ungrounded LLM text makes this worse, not better. A narrative with invented amounts or unexplained conclusions is dangerous in a regulated setting. Dossier is built around one rule: **every claim in a draft must trace back to a source record.**

## What it does

1. **Triage.** Classifies an alert and routes low-risk alerts to a short closure rationale.
2. **Gather evidence.** Pulls the customer profile, transactions, prior cases, behavior statistics, and counterparty network through MCP tools. Numbers are computed in SQL, not by the model.
3. **Match typologies.** Retrieves relevant laundering patterns from a corpus of public guidance, with citations.
4. **Draft.** Writes a structured narrative where every factual sentence cites evidence IDs, and includes mitigating factors and limitations, not just red flags.
5. **Verify.** A grounding check rejects uncited or unsupported claims before a human sees them.
6. **Human review.** The workflow pauses for an analyst to approve, edit, request a redraft, or reject.

## Design principles

- **Human in control.** No disposition without explicit approval. The system never submits a report anywhere.
- **Grounded.** Claim-level citations, a verifier, and exact numbers from tools.
- **Least privilege.** The agent reaches data only through a read-only, role-checked MCP server. PII is masked before anything reaches a model or a trace.
- **Auditable.** Every user action, tool call, and model call is logged with hashes and trace IDs.
- **Measured.** Quality, cost, and latency are evaluated against baselines on a frozen test split, with honest uncertainty.

## Architecture

```
Analyst (browser)
      |
  Streamlit console
      |  HTTPS + JWT
  FastAPI service ---------------------------+
      |                                      |
  Agent worker (LangGraph)             Postgres + pgvector
      |        |                       (data, checkpoints,
      |        +--> Claude API          audit log, vectors)
      |  MCP                                 ^
  MCP server ---------------------------------+
  (tools, resources, masking, role checks)

All services --> Langfuse (traces, cost, eval scores)
```

## Tech stack

| Area | Choice |
|---|---|
| Language | Python 3.11+ (developed on 3.14) |
| Agent orchestration | LangGraph, with a human review interrupt |
| Tool layer | Model Context Protocol (MCP) server |
| LLM | Claude via API: Sonnet for reasoning and drafting, Haiku for triage and verification |
| Retrieval | pgvector with hybrid search and reranking |
| Database | Postgres 17 with pgvector |
| API and UI | FastAPI, Streamlit |
| Observability | Langfuse |
| Quality tooling | pytest, ruff, mypy |
| Deployment | Docker, GitHub Actions, Azure Container Apps |

## Roadmap

- [x] Repository skeleton, tests, linting, and type checks
- [x] Typed, validated configuration with masked secrets
- [x] Postgres with pgvector in Docker, connection helper, and integration tests
- [x] Database schema and migrations
- [x] Load the public IBM synthetic AML transaction dataset
- [ ] Synthetic KYC data generator
- [ ] Rule engine that raises alerts
- [ ] MCP server (read-only tools, masking, audit log)
- [ ] RAG over public typology and regulatory guidance
- [ ] LangGraph agent with grounding verifier and human review gate
- [ ] Evaluation harness with baselines, bias tests, and prompt-injection tests
- [ ] API and analyst console
- [ ] Deployment and CI/CD

## Quick start

Prerequisites: Python 3.11 or later, Docker with Compose, and Git.

```bash
git clone https://github.com/varun-vijayanand/Dossier.git
cd Dossier

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

cp .env.example .env
docker compose -f infra/docker-compose.yml up -d --wait
alembic upgrade head

python -m pytest && ruff check . && mypy src && echo "ALL GREEN"
```

The database listens on `localhost:5433` (host port 5433 maps to Postgres's 5432 inside the container), which avoids clashing with a Postgres you may already run locally. To stop it and keep the data, run `docker compose -f infra/docker-compose.yml down`. Add `-v` only if you want to delete all data.

Integration tests need the database running. If it is not reachable, they skip and print the reason.

## Configuration

Settings are read from environment variables, or from a `.env` file, with the prefix `DOSSIER_`. Copy `.env.example` to `.env` and edit it. Never commit `.env`.

| Variable | Purpose | Default |
|---|---|---|
| `DOSSIER_ENVIRONMENT` | Environment name | `local` |
| `DOSSIER_DATABASE_URL` | Postgres connection URL | `postgresql://dossier:dossier@localhost:5433/dossier` |
| `DOSSIER_ANTHROPIC_API_KEY` | API key for the LLM (kept out of logs) | not set |
| `DOSSIER_MODEL_TRIAGE` | Model for triage and verification | `claude-haiku-5-5` |
| `DOSSIER_MODEL_REASONING` | Model for assessment and drafting | `claude-sonnet-5-5` |
| `DOSSIER_MAX_TOOL_CALLS` | Tool-call limit per investigation run | `25` |
| `DOSSIER_RUN_DEADLINE_SECONDS` | Time limit per investigation run | `120` |

The default database credentials are for local development only.

## Repository layout

```
src/dossier/
  common/       settings, database helpers
  data/         data loading, synthetic generators, rule engine   (planned)
  mcp_server/   MCP tools, resources, masking, audit              (planned)
  rag/          ingestion, retrieval, reranking                   (planned)
  agent/        LangGraph workflow and verifier                   (planned)
  api/          FastAPI service                                   (planned)
  evals/        metrics, judges, safety suites                    (planned)
tests/          unit, contracts, integration
infra/          Docker Compose and deployment files
data/           raw (ignored), processed (ignored), gold set
docs/           design documents and progress notes
```

## Evaluation (planned)

Results will be published here once measured, with three configurations side by side: rules only, a single-prompt LLM, and the full agent. Metrics will include triage recall, faithfulness, citation precision, unsupported-number rate, bias and prompt-injection results, latency, and cost per alert, along with sample sizes and confidence intervals.

## Data

Dossier uses synthetic and public data only. Transactions come from the public IBM synthetic AML dataset, which is downloaded separately and not redistributed in this repository. KYC records are generated. Typology guidance comes from public documents, with sources and licence notes listed in the repo once the corpus is added. No real customer data is used anywhere.

## Limitations

- Synthetic data differs from real bank data, so results will not predict production performance.
- The evaluation set will be small and labeled by one person.
- The India STR template is illustrative and is not an official filing format.
- This is a portfolio and learning project, not a production compliance system.

## Documentation

Design documents (product requirements, technical design, evaluation plan, security and system card, and delivery plan) will live in `docs/`. Day-to-day progress is tracked in `docs/memory.md`, with learning notes in `docs/notes.md`.

## Contributing and conventions

Conventional commit prefixes (`feat:`, `fix:`, `chore:`, `docs:`, `test:`), small commits, and green checks before every commit.

