# Dossier: My Learning Notes (plain language)

These are my own notes. Each completed block gets a section: what we did, why we did it, the key ideas in simple words, and what went wrong and what it taught me. New sections are added at the bottom.

---

## Block 1: Repo skeleton and tooling

### What we did
Created the project folder, turned it into a Git repository, made a private Python environment, laid out the folders, and set up three quality tools. We finished with one tiny test to prove everything is wired up.

### Why
Doing this first means that tests, linting, and version control exist before any real code. They never become "something I will add later".

### Key ideas
- **Virtual environment (`.venv`):** a private folder of Python packages for this project only. Other projects can use different versions without clashing. When it is active, the terminal prompt starts with `(.venv)`.
- **Git:** a save-history system. A **commit** is a saved snapshot with a message. We use message prefixes: `chore:` for housekeeping, `feat:` for a new feature, `fix:` for a bug fix, `test:` for tests.
- **`src/dossier/` layout:** all code lives inside one package called `dossier`. Each subfolder is one part of the system: `mcp_server`, `rag`, `agent`, `api`, `evals`, `data`, `common`. A folder only counts as a package if it has an `__init__.py` file.
- **`.gitignore`:** a list of things Git must never save. Secrets (`.env`), big downloaded data, and auto-generated folders belong here.
- **`pyproject.toml`:** the project's ID card. It holds the name, the libraries it needs (dependencies), tools only needed for development (dev dependencies), and tool settings.
- **Editable install (`pip install -e`):** links the package to my source folder, so my edits take effect immediately without reinstalling.
- **The quality trio:** `pytest` runs tests, `ruff` checks code style and common bugs, and `mypy` checks that the types fit together.
- **Smoke test:** a trivial test that only proves the setup works. If it fails later, the problem is the setup and not my logic.

### What went wrong and what I learned
- I forgot `*.egg-info/` in `.gitignore`, so generated build files got committed. Lesson: after every commit, look at what went in (`git ls-files` or `git show --stat`).

---

## Block 1.5: Cleanup

### What we did
Stopped Git from tracking the generated `egg-info` folder, and added `.gitkeep` files to empty folders.

### Why
Generated files do not belong in history. Git also ignores empty folders, so a tiny `.gitkeep` file makes sure someone cloning the repo gets the full folder structure.

### Key ideas
- `git rm --cached` removes a file from Git's tracking without deleting it from my disk.
- Stage files by name (`git add file1 file2`) when a commit should have one purpose. `git add .` grabs everything, including things I did not mean to include.

---

## Block 2: Typed settings

### What we did
Wrote `src/dossier/common/config.py`, one class that holds every setting: the database URL, the API key, the two model names, and run limits. Added `.env.example` and four tests.

### Why
Without this, settings get scattered as `os.getenv` calls and hardcoded strings. That is how secrets leak and bugs hide. With one validated settings class, a wrong value fails at startup with a clear error, and not halfway through a run.

### Key ideas
- **pydantic-settings** fills each field from, in order: real environment variables, then the `.env` file, then the default written in code.
- **`env_prefix="DOSSIER_"`:** the field `max_tool_calls` is set with `DOSSIER_MAX_TOOL_CALLS`. The prefix avoids clashes with other programs.
- **`SecretStr`:** hides the value when printed. The key shows as `**********` in logs and errors, and I must call `.get_secret_value()` on purpose to read it.
- **`Field(ge=1)`:** rejects impossible values, such as a limit of zero.
- **`lru_cache` on `get_settings()`:** build the settings once and reuse them everywhere.
- **`.env` vs `.env.example`:** `.env` is my private file with real secrets and is ignored by Git. `.env.example` is a committed template that lists the variables without secrets.
- **Model tiers:** Haiku for cheap, high-volume steps (triage, verification), Sonnet for reasoning and drafting. Because the names live in settings, switching models is a config change and not a code change.
- **Test tools:** `monkeypatch` sets an environment variable for one test and then undoes it. `_env_file=None` stops my real `.env` from changing test results.

### What went wrong and what I learned
- The command `cp .env.example .env` failed because the file was created with a space in its name (`.env .example`). Git showed it in quotes, which was the clue. Lesson: quotes around a name in `git status` often mean a space is hiding in it.
- I ran a commit with red tests, because my commands were a plain list and not chained. Lesson: chain checks with `&&` (`pytest && ruff check . && mypy src && echo "ALL GREEN"`), so a later step only runs if the earlier one passed.

---


## Block 3: Postgres with pgvector in Docker

### What we did
Started a Postgres database inside Docker, with the pgvector add-on for storing and comparing vectors. Wrote a small helper that opens a connection from Python, and two tests that prove the connection works and that vector distance works.

### Why
The design keeps everything in one database: the alert data, the agent's saved state, and the vectors for searching typology documents. Docker gives me a disposable, repeatable database without installing Postgres on my Mac. The tests prove the whole chain works before I build tables on top of it.

### Key ideas
- **Image, container, volume:** an image is the packaged recipe, a container is a running copy of it, and a volume is where the data is stored so it survives when the container is removed.
- **Docker Compose:** one file (`infra/docker-compose.yml`) describes the setup, so one command starts everything the same way every time.
- **Healthcheck and `--wait`:** "running" does not mean "ready". The healthcheck asks Postgres if it can take connections, and `up -d --wait` waits for a yes. My first `psql` call failed because I ran it too early.
- **Port mapping (`5433:5432`):** the number on the left is the port on my Mac, the number on the right is the port inside the container. I changed only the left side.
- **Compose project name (`name: dossier`):** Compose labels what it creates with this name. If I rename it, the old resources stay behind under the old name and need `docker compose -p oldname down`.
- **pgvector:** adds a vector type and distance operators. The `<->` operator gives the straight-line distance between two vectors, which is what similarity search uses later for RAG.
- **Connection helper (`db.py`):** the one place in the code that knows how to open a database connection, using the validated settings from Block 2.
- **Integration tests:** tests that need a real service running. They carry an `integration` marker, so I can run only the fast tests with `-m "not integration"`.
- **`&&` chaining:** a step only runs if the one before it passed.

### What went wrong and what I learned
- **Two databases on port 5432:** my Mac already ran a Homebrew Postgres. Python connecting to `localhost` reached that one, which had no `dossier` user. Testing from inside the container (`docker exec`) worked, but that does not test the route from my Mac. Lesson: test the same route the real code will use. `lsof -nP -iTCP:5432 -sTCP:LISTEN` shows who is listening on a port.
- **Skipped is not passed:** the tests were skipped, hiding the real error. Putting the error text in the skip message exposed it. Lesson: a skip needs a reason you can read.
- **`import dossier` kept failing:** `pip list` said the package was installed, but Python could not import it. The cause was a macOS "hidden" flag on the venv files, which Python skips for the link file. Fixes: `chflags -R nohidden .venv`, and `pythonpath = ["src"]` in the pytest settings as a safety net. Lesson: test the real thing (`python -c "import dossier"`), not just the package list.
- **The terminal stuck on `~` and `(END)`:** that was a pager. Press `q` to leave it, or use `-P pager=off`.
- **Docker command not found:** an old terminal tab had not picked up the new PATH. Opening a new tab fixed it.
- **`git status` columns:** a leading space before `M` means "changed but not staged". I staged by name and missed a file. Lesson: read the status output again before every commit.

## Block 4: database schema and migrations

### What we did
We gave the database a blueprint that lives in code, and a tool to apply it. The tool is Alembic. The blueprint is migration `0001`, which switches on pgvector and creates two empty tables: `accounts` and `transactions`.

### Why
- **Migrations instead of typing `CREATE TABLE` by hand.** Typed commands leave no record. If I delete the Docker volume, set up a new Mac, or deploy to Azure, one command (`alembic upgrade head`) rebuilds the exact same database.
- **Plain SQL, no ORM.** I write the SQL myself, so pgvector columns and extensions stay simple and I can see exactly what runs.
- **Undo works.** I ran `downgrade base` and then `upgrade head` and got the same tables back. A recipe that has never been undone can't be trusted, and the tables were empty, so it cost nothing. Never repeat this once real data is loaded: the downgrade deletes it.
- **Tests for the schema.** If someone changes a table and forgets to run the migration, a test fails now instead of the app failing later.

### Why these design choices
- **`numeric(24,4)` for money.** It is exact. Floats can drift when you add them up.
- **`timestamp` without a time zone.** As far as I know the IBM data has no zone, and I didn't want to invent one.
- **`is_laundering` is the answer key.** It is the ground truth from the synthetic data. I use it to grade Dossier. The agent must never be able to read it, or it would be cheating on its own test. I will enforce that in the MCP server block.
- **No indexes and no foreign keys yet.** Loading millions of rows into an already-indexed table is much slower, so indexes come after the load in a later migration.
- **Composite primary key on `accounts`.** A transaction names a bank and an account, so the pair `(bank_id, account_number)` is the safest identity until I have seen the real data.

### How Alembic connects to my settings
`migrations/env.py` calls `get_settings()` for the database URL. My URL starts with `postgresql://`, but SQLAlchemy would then look for the old `psycopg2` driver, so `env.py` rewrites it to `postgresql+psycopg://` in memory. `.env` and `config.py` are untouched, and no password is stored in any Alembic file.

### What went wrong and what I learned
1. **`import dossier` failed inside Alembic.** The macOS `hidden` flag was back on the `.pth` file that links my package into the venv. Python skips hidden `.pth` files. Fix: `chflags -R nohidden .venv`.
2. **The flag came back by itself.** It returned without a reinstall, so my earlier note that it "did not return" was wrong. I suspect iCloud Desktop sync but have not confirmed it.
3. **A safety net.** I added `prepend_sys_path = .:src` to `alembic.ini` (pytest already had its own `pythonpath = ["src"]`). I proved it works by hiding the `.pth` file on purpose: plain Python failed to import `dossier`, but Alembic still ran.
4. **Wrong mypy command.** The mentor suggested `mypy .`, which also checks the tests and showed 5 errors in `tests/unit/test_config.py`. My real command is `mypy src`. The errors come from mypy not understanding pydantic settings without its plugin (with the plugin they all disappear). So my tests have never been type-checked. Adding the pydantic plugin to `pyproject.toml` and checking tests too is an optional cleanup.
5. **Skipped is not passed.** When Docker Desktop was off, the 2 integration tests showed `skipped`. A block is only complete when they show as passed.
6. **I missed a file.** `migrations/README` was left out of the first commit, so I added it separately. Lesson: read the `ls` and `git status --short` output before committing.

### Where this fits in the whole project
Every later block sits on this one. Block 5 loads the IBM data into these tables. Block 6 adds KYC tables as migration `0002` and later. Block 7 reads the transactions to produce alerts. The MCP server and the agent gather evidence by querying these tables, and RAG uses the pgvector extension. For the Mastercard role, a repo that builds its own database from versioned, tested migrations looks like production engineering and not a notebook.

### Things to remember
- The columns are written from the mentor's memory of the IBM dataset. Block 5 must check them against the real CSV. If they differ, add `0002`. Never edit `0001`.
- Start Docker Desktop before running tests.
- Check iCloud "Desktop & Documents Folders" before Block 5, and move the project to `~/dev/dossier` if it is on.
