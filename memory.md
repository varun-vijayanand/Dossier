
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
