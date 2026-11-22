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

### 2026-11-21: Block 4 complete (Alembic migrations and core schema)

- **What exists now:** Alembic is set up with plain-SQL migrations (no ORM models). Migration `0001` enables the `vector` extension and creates two empty tables: `accounts` and `transactions`. The database is at `0001 (head)`.
- **Files added:** `alembic.ini`, `migrations/env.py`, `migrations/script.py.mako`, `migrations/README`, `migrations/versions/0001_pgvector_extension_and_core_tables.py`, `tests/integration/test_schema.py`.
- **How the connection works:** `migrations/env.py` reads the URL from `get_settings()` and rewrites `postgresql://` to `postgresql+psycopg://` in memory only. `.env` and `config.py` are unchanged. The `sqlalchemy.url` line in `alembic.ini` is unused, so never put credentials there.
- **Import safety net:** `prepend_sys_path = .:src` in `alembic.ini`. Tested by hiding the editable-install `.pth` file: plain Python failed to import `dossier`, but `alembic current` still worked.
- **Tests:** 11 pass (5 unit, 6 integration), with no skips. ruff and `mypy src` are clean. 4 new integration tests check: database at latest migration, `vector` extension present, both tables exist, `transactions` columns in the right order.
- **Commits:** d876379 (Block 4 main commit), 1760c73 (README stub added afterwards).
- **Versions seen:** alembic 1.20.1, SQLAlchemy 2.1.9, psycopg 3.3.9, mypy 2.4.1, pydantic 2.14.3, pydantic-settings 2.16.3. Alembic and SQLAlchemy are newer than the mentor's knowledge, so check current docs before using anything beyond the basics.
- **Commands:**
  - Apply migrations: `alembic upgrade head`
  - Show current version: `alembic current`
  - Preview the SQL without running it: `alembic upgrade head --sql`
  - Undo everything (only while tables are empty): `alembic downgrade base`
- **Known issues and lessons:**
  1. The macOS `hidden` flag returned on the venv `.pth` file without any reinstall (the file date was unchanged). This corrects the Block 3 note that it "did not return". Cause not confirmed; suspected iCloud Desktop sync. Fix: `chflags -R nohidden .venv`.
  2. The `transactions` and `accounts` columns were written from the mentor's memory of the IBM AML dataset, not from the real CSV. Block 5 must compare them with the actual headers. If they differ, add migration `0002`. Never edit `0001` once applied.
  3. The real check command is `pytest -q && ruff check . && mypy src && echo "ALL GREEN"`. The mentor wrongly suggested `mypy .`, which type-checks the tests and shows 5 errors in `tests/unit/test_config.py`. These are not real regressions: the pydantic mypy plugin clears them. Optional cleanup for later.
  4. Docker Desktop must be running before tests. If integration tests show `skipped`, the database is unreachable.
- **Open question:** is iCloud "Desktop & Documents Folders" turned on? If yes, move the project to `~/dev/dossier` before Block 5.
- **Next up:** Block 5, load the IBM AML data (check the real CSV headers first, bulk load, then add indexes in a new migration). After that: Block 6 (synthetic KYC), Block 7 (rule engine and alerts), then the MCP server.

### 2026-11-21: Block 5 complete (IBM AML data loaded, bank-id fix, indexes)

- **Project moved.** The project now lives at `~/dev/dossier` (it was `~/Desktop/Dossier`, which iCloud syncs). The venv was rebuilt from a saved `pip freeze` file. Open terminals in `~/dev/dossier`, then `source .venv/bin/activate`. GitHub: https://github.com/varun-vijayanand/Dossier
- **Data loaded (HI-Small):** 518,581 accounts, 5,078,345 transactions, 5,177 with `is_laundering` true. Timestamps run 2022-09-01 to 2022-09-18. Matches the published figures exactly.
- **Raw files:** `data/raw/` (git-ignored, never commit): `HI-Small_Trans.csv` (454 MB), `HI-Small_accounts.csv` (32 MB), `HI-Small_Patterns.txt` (316 KB). `data/raw_old/` holds an earlier wrongly labelled download and can be deleted.
- **Loader:** `src/dossier/ingest/ibm_aml.py`. Run `python -m dossier.ingest.ibm_aml accounts` or `... transactions` (optional second argument: a CSV path). Streams the CSV with COPY, refuses to run if the table already has rows, runs as one transaction (all or nothing).
- **Migration 0002:** generated columns `from_bank_id` and `to_bank_id` on `transactions` = the bank code with leading zeros removed (`ltrim(..., '0')`). The raw `from_bank` / `to_bank` are kept exactly as loaded.
- **Migration 0003:** indexes `ix_transactions_from_account` (from_bank_id, from_account, ts), `ix_transactions_to_account` (to_bank_id, to_account, ts), `ix_accounts_entity` (entity_id), then ANALYZE. About 400 MB of indexes, database total 1,247 MB.
- **Measured speed:** typical account lookup 283 ms to 0.56 ms (sequential scan to index scan). A hub account (about 170,000 rows) 321 ms to 196 ms.
- **Tests:** 17 pass (5 unit, 12 integration), no skips. New: `tests/integration/test_ingest.py` (5 tests on temporary tables) and an index-exists test in `test_schema.py`. The schema test column list now includes `from_bank_id` and `to_bank_id`. Check chain: `pytest -q && ruff check . && mypy src && echo "ALL GREEN"`.
- **Commits:** 9c2705b (migration 0002), a384018 (loader), 5cc929d (migration 0003), 6d8a9fd (loader tests).
- **Migration 0001 was NOT changed.** The columns guessed from memory matched the real CSV headers.
- **Rules for all later code:**
  1. Join `transactions` to `accounts` on the trimmed bank id AND the account number together: `t.from_bank_id = a.bank_id AND t.from_account = a.account_number`. Never on account number alone (50 extra matches appear, so account numbers repeat across banks). Never on bank name (30,470 bank ids but only 20,053 bank names).
  2. `is_laundering` is the answer key. The agent and MCP tools must never read it.
  3. One account sent about 168,000 transactions. MCP tools must return summaries first (counts, totals, top counterparties, date range) and capped, paged detail on request, never "all rows".
- **Patterns file (not loaded, on purpose):** 370 patterns (cycle 54, gather-scatter 51, bipartite 49, fan-out 48, scatter-gather 44, stack 43, random 41, fan-in 40) and 3,579 transaction rows. The rows have no transaction id, so linking them needs matching on contents (time, banks, accounts, amounts), including the zero-padding fix. If every row is distinct and matches, about 69% of the 5,177 laundering labels belong to a named pattern (unverified). Decision: load it in the evaluation block, in its own tables that the agent's database role cannot read.
- **Lessons:**
  1. The first download had mislabelled files (the accounts data was named like the transactions file, and no transactions file existed). Caught by checking line counts and the first lines before loading. Always verify a download that way.
  2. The join check after loading found 5,078,345 of 5,078,345 senders unmatched. That was zero-padded bank codes in one file, found only because we tested a join before building on the data.
  3. Packages installed while building belong in `pyproject.toml` the same day (alembic and sqlalchemy had been missed). A throwaway fresh venv install is the check.
  4. The macOS hidden flag on the venv `.pth` file was clean after the rebuild outside iCloud. Still watch for it (`ls -lO .venv/lib/python3.14/site-packages | grep -iE "pth|dossier"`).
- **Open items:** shared test fixtures in a `conftest.py` (the `conn` fixture is duplicated in two files). Optional: pydantic mypy plugin so tests can be type-checked. The five planning documents sit in the repo root and could move to `docs/`. `data/raw_old/` can be deleted.
- **Next up:** Block 6, synthetic KYC data (customer profiles for the entities in `accounts`, as migration 0004 and later). Then Block 7 (rule engine and alerts), then the MCP server.
