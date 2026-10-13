# AGENTS.md

Instructions for **any** AI coding agent working in this repo (Claude Code, Codex,
Cursor, Copilot, Gemini, Aider...). Humans should read it too. `CLAUDE.md` imports
this file, so keep the shared rules here and put tool-specific notes in that tool's file.

## Project in one paragraph

`fashion-search` is a fashion visual search and zero-shot tagging app. It embeds
clothing photos with **Marqo-FashionSigLIP**, a fashion-specific vision-language
model, and auto-tags each one by category, colour, pattern, sleeve and style. It
then serves text search, image search, tag browsing and optional virtual try-on
(FASHN VTON v1.5) through a FastAPI backend and a React "Mirror" web app (`web/`). There's
also a Gradio developer UI. It replaces the 2025 Fashion-MNIST MLP in `legacy/`.

## The docs system: read first, update last

| File | What it holds | When to update it |
|---|---|---|
| `docs/PROGRESS.md` | Current status, task board, handoff log | **Every session**: read at start, append a handoff entry at end |
| `docs/ARCHITECTURE.md` | Modules, data flow, file formats, invariants | Whenever you add, move or rename a module or change a file format |
| `docs/DECISIONS.md` | Numbered decision records (ADRs) | Whenever you pick between real alternatives (model, library, layout, data policy) |
| `CHANGELOG.md` | User-visible changes per version | Any change a user of the app or CLI would notice |

**Session protocol**
1. **Start:** read `docs/PROGRESS.md` (the "Now" section and the last 2 handoff entries). Then read `docs/ARCHITECTURE.md` if you'll touch code.
2. **Before a significant choice:** check `docs/DECISIONS.md` so you don't re-argue a settled decision. To reverse one, add a new ADR that supersedes it. Never edit an old ADR's decision.
3. **End:** move finished tasks on the board, then append a handoff entry with the date, the agent, what was done, what's next and any open problems. Unfinished work must be described well enough that a different agent can pick it up cold.

## Commands

Run everything from the repo root with the project venv (`.venv/`).

```bash
# setup (once)
python -m venv .venv
.venv/Scripts/python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/pre-commit install

# daily
.venv/Scripts/fashion-search index      # embed + tag data/shirts -> artifacts/index
.venv/Scripts/fashion-search serve      # web app + API on http://127.0.0.1:8000 (needs web/dist)
npm --prefix web run dev                # frontend dev server on :5173 (proxies to :8000)
.venv/Scripts/fashion-search app        # Gradio developer UI on http://localhost:7860
.venv/Scripts/fashion-search evaluate   # writes reports/results.md (~3 min on GPU)

# optional virtual try-on (~2 GB weights, ~8 GB VRAM)
.venv/Scripts/python -m pip install -e ".[tryon]"
.venv/Scripts/fashion-search tryon-download
.venv/Scripts/fashion-search tryon --person p.jpg --garment g.jpg --out out.png

# checks (must pass before every commit; CI runs the same)
.venv/Scripts/ruff check . && .venv/Scripts/ruff format --check .
.venv/Scripts/pytest                    # fast tests, no model download
.venv/Scripts/pytest -m slow            # also loads the real model (~800 MB first time)
npm --prefix web run lint && npm --prefix web run typecheck && npm --prefix web test
```

On Linux or macOS, replace `.venv/Scripts/` with `.venv/bin/`.

## Repo layout

```
src/fashion_search/   the package (see docs/ARCHITECTURE.md for each module)
web/                  React + TypeScript frontend (Vite); web/src/lib/api.ts mirrors api.py's models
tests/                pytest; fast tests use fake embeddings, slow tests use the real model
data/                 local data, git-ignored (see data/README.md for how to get it)
artifacts/index/      generated embeddings + tags, git-ignored, rebuilt by `fashion-search index`
reports/              committed evaluation results
legacy/               the original 2025 notebook; read-only, do not modernise
docs/                 the docs system above
```

## Rules

- **Only `core.py` loads the search model, and only `tryon.py` touches `fashn_vton` (lazily).** `catalog.py`, `taxonomy.py` and `cli.py` must stay importable without loading any model, so tests and `--help` stay fast. Try-on is optional, so everything must still work when it isn't installed.
- **API changes go in both places:** update the pydantic models in `api.py` and the types in `web/src/lib/api.ts` in the same commit, and add an API test.
- **Fast tests must not download anything.** Anything that needs the model or a dataset gets `@pytest.mark.slow`.
- **Never commit** `data/`, `artifacts/`, `.venv/`, model weights or secrets. The shirt photos come from third-party marketplace listings, so they are not ours to publish (ADR-004).
- **Don't change `legacy/`** except to fix links. It's a historical record.
- **Changing tags:** edit `taxonomy.py`, rerun `fashion-search index`, and spot-check a few images before claiming the tags are good.
- **Reporting results:** report evaluation numbers exactly as the script printed them, including the ones that look bad. `reports/results.md` is generated, so don't hand-edit it.
- **Style:** ruff (line length 100), type hints on public functions, short docstrings, and comments that explain *why*. Match the surrounding code.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`). Keep each commit to one logical change, and use a branch plus a PR for anything non-trivial (see `CONTRIBUTING.md`).
- **Ask the human first** before pushing, creating GitHub repos, changing licences, adding large dependencies or deleting data.

## Environment facts

- Dev machine: Windows 11, RTX 4060 Laptop (8 GB VRAM), Python 3.12, CUDA 12.6 wheels.
- The model loads from the Hugging Face cache (`~/.cache/huggingface`). The first run downloads about 800 MB.
- Everything also runs on CPU, just more slowly. `DEVICE` is auto-detected in `core.py`.
- Paths are set in `src/fashion_search/config.py` and can be overridden with `FASHION_*` environment variables.
