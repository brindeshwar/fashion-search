# Contributing

## Setup

Follow the Quickstart in [README.md](README.md), then run:

```bash
.venv/Scripts/pre-commit install
```

## Workflow

1. **Pick or create an issue.** Use the bug or feature template. For agents, the task board in `docs/PROGRESS.md` is the source of truth.
2. **Branch from `main`:** `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>`.
3. **Make the change, with tests.** New logic needs a fast test. Anything that needs the model gets `@pytest.mark.slow`.
4. **Check locally:**
   ```bash
   .venv/Scripts/ruff check . && .venv/Scripts/ruff format --check .
   .venv/Scripts/pytest
   ```
5. **Update the docs:**
   - `CHANGELOG.md` under _Unreleased_, if users would notice the change
   - `docs/ARCHITECTURE.md` if modules or file formats changed
   - `docs/DECISIONS.md` if you chose between real alternatives
   - `docs/PROGRESS.md`: the task board and a handoff entry
6. **Commit** using [Conventional Commits](https://www.conventionalcommits.org/): `feat: add try-on tab`, `fix: normalise validation set`.
7. **Open a PR** and fill in the template. CI must pass before merge. Squash-merge into `main`.

## Releases

1. Move the _Unreleased_ entries in `CHANGELOG.md` to a new version heading.
2. Bump `version` in `pyproject.toml` and `src/fashion_search/__init__.py`.
3. Tag the release: `git tag v0.X.0 && git push --tags`.

## Code style

ruff handles lint and formatting (line length 100). Use type hints on public functions
and short docstrings. Comments explain *why*, not *what*. Keep torch imports inside
`core.py` (see `AGENTS.md` → Rules).
