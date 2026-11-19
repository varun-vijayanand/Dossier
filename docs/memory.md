# Dossier: Project Memory (progress tracker)

How to use this file: it is an append-only log. The **newest entry at the bottom is the current state**. At the start of a new session, paste this file to Claude so we can pick up exactly where we stopped.

## What this is

Dossier is an AI assistant for AML (anti-money-laundering) alert investigation. For each alert it gathers evidence through an MCP server, matches the activity to known laundering patterns using RAG, and drafts a cited, India-STR-style narrative. A human approves everything. It is project 1 of 3 in a portfolio aimed at the Mastercard Data Scientist I (Pune) role. It uses synthetic and public data only.

## How we work

- Mentor and mentee: Claude is the mentor, I am the mentee.
- Small code blocks, each with a plain explanation of what it does and why.
- A block counts as complete only when tests, lint, and type checks all pass (chained with `&&`) and the work is committed. After that, Claude gives an update for this file and for `docs/notes.md`.
- Stage commits by file name, not `git add .`, and check `git status --short` for `.env` or `.egg-info` before committing.

## Environment

- Machine: MacBook Air (Apple silicon), macOS, zsh
- Project folder: `~/Desktop/Dossier` (may move to `~/dev/dossier` if the hidden-flag problem returns)
- Python 3.14.6 in a venv at `.venv` (activate with `source .venv/bin/activate`)
- Docker Desktop: Docker 29.9.3, Compose v5.7.0
- A Homebrew `postgresql@16` also runs on this Mac and listens on port 5432, which caused a conflict (see log)
- Pre-flight check passed: langgraph, langgraph-checkpoint-postgres, mcp, anthropic, fastapi, streamlit, psycopg, pgvector, and langfuse all resolve on Python 3.14. Versions seen: mcp 2.3.0, langgraph 1.2.23, langfuse 5.2.0. These are newer than the mentor's knowledge, so check current docs before writing code for them.

## Decisions

- Dataset: IBM synthetic AML transactions for the MVP, Project 0 data later as a stretch
- LLM: Claude through the API. Sonnet 5.5 for reasoning and drafting, Haiku 5.5 for triage and verification. GPT-6 Sol or Luna as an optional comparison arm
- Orchestration: LangGraph with a human review gate. Tools exposed through an MCP server
- Database: one Postgres with pgvector (data, checkpoints, vectors)
- UI: Streamlit for the MVP, FastAPI backend
- Cloud: Azure Container Apps (scale to zero). Optional short AWS run
- Report format: India STR is primary, FinCEN SAR is secondary
- Observability: Langfuse

## Planning documents (Claude Docs)

- PRD: https://claude.ai/artifact/28mgj3cyufxkVaqfNuYurC
- Technical Design: https://claude.ai/artifact/QjBjcKJPd2Gg5Z1T8mtySG
- Evaluation and Test Plan: https://claude.ai/artifact/G8Czdqt2MLp3BU8o4SqsBr
- Security, Compliance, and System Card: https://claude.ai/artifact/NEhwQJobrJo2bszFTSpMjw
- Delivery Plan and Backlog: https://claude.ai/artifact/CCQs4XzTqEUEsKKeoJiaRg
- Project Definition (original, timeline there is the aggressive case): https://claude.ai/artifact/TFRbMKHLLRrymfW4pFHTAx

## Progress log (newest at the bottom)

### 2026-11-19: Blocks 1, 1.5, and 2 complete

- **Block 1, repo skeleton and tooling:** git repo, venv, `src/dossier/` package layout, `.gitignore`, `pyproject.toml`, a smoke test. pytest, ruff, and mypy all pass. Commit `f0dfb06` "chore: project skeleton".
- **Block 1.5, cleanup:** `*.egg-info/` added to `.gitignore` and removed from Git tracking, `.gitkeep` files added to keep empty folders. To confirm: `git ls-files` should show no `.egg-info`.
- **Block 2, typed settings:** `src/dossier/common/config.py` (pydantic-settings), `.env.example` committed, `.env` private and ignored, 4 unit tests. Commit message "feat: typed settings with validation".

### 2026-11-19: Block 3 in progress (NOT complete)

Goal: Postgres with pgvector in Docker, plus a Python connection helper and integration tests.

Done so far:
- `infra/docker-compose.yml` with project name `dossier`, image `pgvector/pgvector:pg17`, healthcheck, and a named volume. The container is healthy.
- `src/dossier/common/db.py` (`connect()` helper) and `tests/integration/test_db.py` (2 tests). Commit `49ecf14`, which was made before the tests ran green.
- The `integration` marker is registered in `pyproject.toml`.

Open issues:
1. **Port conflict:** Homebrew `postgresql@16` holds `127.0.0.1:5432`, so Python reaches it instead of the Docker database and gets `role "dossier" does not exist`. Plan: map Dossier's database to port 5433 (compose file, `.env`, `.env.example`, and the default in `config.py`).
2. **Editable install keeps breaking:** `import dossier` fails after installs. Cause found: the venv folders and the `.pth` file carry the macOS `hidden` flag, which recent Python versions skip. Mitigations so far: `chflags -R nohidden .venv` and `pythonpath = ["src"]` in the pytest config. Still to confirm: that the `pythonpath` line is in `pyproject.toml`, whether iCloud Desktop sync is on, and whether the flag comes back after the next `pip install`.
3. The two integration tests currently skip. They must show as passed before Block 3 is called complete.

Next up: finish Block 3, then Block 4 (database schema and migrations), Block 5 (load the IBM AML data), Block 6 (synthetic KYC), Block 7 (rule engine and alerts), then the MCP server.

### 2026-11-19: Block 3 complete (Postgres with pgvector in Docker)

- The database runs in Docker: image pgvector/pgvector:pg17, compose project name dossier, container dossier-db, volume dossier_dossier_pgdata. From my Mac it is at localhost:5433 (host port 5433 maps to container port 5432).
- The Homebrew postgresql@16 still runs on port 5432, so Dossier avoids that port.
- Code added: src/dossier/common/db.py (connect helper) and tests/integration/test_db.py (connection test and a pgvector distance test).
- Results: 7 tests pass (5 unit, 2 integration). ruff and mypy are clean.
- Commits: 49ecf14 (db helper, made before tests were green), 234a72f (port 5433 and pytest src path), plus the .env.example commit.
- Start the database: docker compose -f infra/docker-compose.yml up -d --wait
- Stop it and keep the data: docker compose -f infra/docker-compose.yml down. Add -v only to delete all data.
- Known issue, checked after a reinstall: the macOS "hidden" flag on venv files can make Python skip the editable-install link. Fix: chflags -R nohidden .venv. Safety net: pythonpath = ["src"] in the pytest settings. The flag did not return after a reinstall.
- Next up: Block 4, the database schema and migrations.
