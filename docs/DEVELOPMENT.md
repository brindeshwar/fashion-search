# Development guide

How to work on the code. For installing, see [SETUP.md](SETUP.md); for how the pieces fit
together, see [ARCHITECTURE.md](ARCHITECTURE.md). AI coding agents should also follow
[AGENTS.md](../AGENTS.md).

## Dev setup

After [SETUP.md](SETUP.md) steps 1–2:

```bash
.venv/Scripts/python -m pip install -e ".[dev]"     # add ",tryon" to work on try-on
.venv/Scripts/pre-commit install                    # runs ruff and file checks on every commit
npm --prefix web ci
```

## Dev loop

Run the backend and the Vite dev server side by side:

```bash
.venv/Scripts/fashion-search serve        # API on http://127.0.0.1:8000
npm --prefix web run dev                  # UI on http://localhost:5173, hot reload
```

Vite proxies `/api` and `/images` to port 8000, so open **:5173** while developing.
`serve` doesn't reload on Python changes; restart it after editing `src/`.

## Checks

These must pass before every commit. CI runs the same ones.

```bash
# Python
.venv/Scripts/ruff check . && .venv/Scripts/ruff format --check .
.venv/Scripts/pytest                      # fast tests: fake embeddings, no downloads (~5 s)
.venv/Scripts/pytest -m slow              # real models (needs the ~800 MB model; try-on test needs [tryon])

# Web
npm --prefix web run lint
npm --prefix web run typecheck
npm --prefix web test
npm --prefix web run build
```

| CI job (`.github/workflows/ci.yml`) | Runs |
|---|---|
| `lint` | ruff check and format |
| `test (3.10)`, `test (3.12)` | fast pytest and `fashion-search --help`, CPU-only torch |
| `web` | npm ci, lint, typecheck, Vitest, build |

## Testing approach

- **Fast tests never load a model.** `tests/conftest.py` provides a 4-item catalogue with
  hand-made embeddings. The API tests inject fake `embed_text` and `embed_image` functions into
  `create_api()` and monkeypatch `tryon.try_on`.
- **Slow tests** (`@pytest.mark.slow`) load the real FashionSigLIP model and, if installed,
  the real try-on pipeline. Run them after changing `core.py` or `tryon.py`.
- **Frontend tests** (Vitest and Testing Library) cover components and helpers in isolation;
  `fetch` isn't mocked globally, so keep network calls in `lib/api.ts` and test logic around them.

## Common changes

### Changing the tags

1. Edit `ATTRIBUTES` in `src/fashion_search/taxonomy.py`. Each attribute is a prompt template
   with one `{}` plus a list of values.
2. Rebuild the index: `fashion-search index`.
3. **Look at the results.** Render a few photos with their new tags and check them by eye;
   label counts alone don't tell you whether the tags are right.
4. If you add or rename an attribute, update `TagName` and the `FILTERS` list in
   `web/src/components/Wardrobe.tsx`, plus the item fields in `tests/conftest.py`.

### Changing the API

1. Change the route or the pydantic model in `src/fashion_search/api.py`.
2. Change the matching types and functions in `web/src/lib/api.ts` **in the same commit**.
3. Add or update a test in `tests/test_api.py`.
4. Update [API.md](API.md).

### Changing the try-on defaults

Defaults live in three places that must agree: `tryon.try_on()`, the `tryon` CLI arguments in
`cli.py`, and `App.tsx` (initial `settings`). Record the reason in a new ADR. ADR-008 shows how
an evidence-based change was documented.

### Using a different search model

Set `FASHION_MODEL_ID` to any OpenCLIP `hf-hub:` model and rebuild the index. Embedding size
is read from the model, so nothing else needs to change. Rerun `fashion-search evaluate` to
compare.

## Project conventions

- **Style:** ruff with line length 100; type hints on public functions; short docstrings;
  comments that explain *why*. TypeScript runs in strict mode, with oxlint.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`,
  `docs:`, `refactor:`, `test:`, `chore:`. Mark breaking changes with `!`.
- **Branches:** `feat/…`, `fix/…`, `docs/…`, `chore/…`, branched from `main` and merged by PR.
- **Never commit** `data/`, `artifacts/`, `.venv/`, `web/node_modules/`, `web/dist/`,
  model weights or secrets.

## Releasing

1. In `CHANGELOG.md`, move the _Unreleased_ entries under a new `## [x.y.z] - YYYY-MM-DD` heading.
2. Bump the version in `pyproject.toml`, `src/fashion_search/__init__.py` and `web/package.json`.
3. Merge to `main` via PR, then tag and publish:
   ```bash
   git tag -a vx.y.z -m "vx.y.z" && git push origin vx.y.z
   gh release create vx.y.z --title "vx.y.z" --notes "<changelog section>"
   ```
4. Update `docs/PROGRESS.md` (status line and a handoff entry).
