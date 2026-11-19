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

*Block 3 notes (Postgres with pgvector in Docker) will be added here once it is complete.*
