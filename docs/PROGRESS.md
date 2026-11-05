# Progress and handoff

Read **Status**, **Now** and the latest handoff entry at the start of every session, and
update them at the end (see `AGENTS.md` → Session protocol). Keep this file short: when the
handoff log grows past about three entries, move the older ones to `docs/history/`.

## Status

**Version:** 1.1.1 · **Status:** complete (concluded with the user on 2026-11-05). Feature
work is finished; only dependency updates are expected. **Health:** green: every feature
was verified end to end on the RTX 4060, and unit, API and browser tests pass in CI.

## Task board

### Done in v1.1 (agreed with the user on 2026-10-24, one PR each)
- [x] **Clean garments before try-on:** BiRefNet on CPU, cached, on by default (ADR-011)
- [x] **Persist looks** (SQLite + PNG files) so they survive a server restart
- [x] **Upload your own garments** in the web app (delete applies to uploads only), with incremental indexing (ADR-012)
- [x] **One-command start scripts** (`start.ps1` / `start.sh`)
- [x] **Browser end-to-end test** (Playwright) in CI, plus a screenshot script
- [x] **Screenshot of a finished try-on** for the README and user guide (no blur needed)

### Now
- _(nothing: the project is complete)_

### Possible future work
Not planned; listed so a future contributor knows where to start.
- Tag accuracy report: hand-label ~50 photos and publish per-tag accuracy in `reports/`
- Run `start.sh` end to end on Linux/macOS (only syntax-checked so far; WSL would do)
- GPU garment cleaning on cards with more than 8 GB, or the 213 MB BiRefNet `swin_v1_tiny` variant (ADR-011)
- Docker image and a public demo (needs a licensed catalogue, see ADR-004)

### Skipped by the user (2026-10-24)
- Docker image: not needed for local use; the start scripts cover it
- Tag accuracy report: maybe later
- Licensed demo catalogue from the user's own clothes: the user doesn't want to share their wardrobe

### Done
- [x] v0.1.0: zero-shot tagging, search, old-vs-new evaluation, professional repo setup
- [x] v0.2.0: virtual try-on (FASHN VTON v1.5), GPU pose fix, "model" photo-type default
- [x] v0.3.0: Mirror web app (React + FastAPI), combined search, async try-on jobs
- [x] v1.0.0: removed Gradio, reorganized docs (user, setup, API and development guides), dependency updates, releases tagged
- [x] v1.1.0: garment cleaning, saved looks, your own garments, one-command start, Playwright e2e + CI, real screenshots, combined dependency updates
- [x] v1.1.1: dependency updates (#28); project concluded

## Known issues
- Try-on is still poor on heavily wrinkled garments photographed on beds; garment cleaning removes backgrounds, props and text but can't fix the garment's shape.
- Try-on slows to 10+ min when another process holds the GPU (the Windows driver spills to RAM). `/api/health` warns about this.
- Tags are zero-shot and haven't been measured against hand labels. Bright colours on multi-colour prints are sometimes tagged "multicolored".
- Queued or running try-ons are lost if the server restarts mid-job (finished ones are saved as looks).
- The first try-on of each garment takes ~15 s longer while it's cleaned on the CPU (then cached).

## Handoff log
Newest first. Older entries: [`history/handoffs-2026-10.md`](history/handoffs-2026-10.md).

```
### YYYY-MM-DD · <agent/person>
**Did:** ...
**Next:** ...
**Watch out:** ...
```

### 2026-11-05 · Claude Code (Opus 5.5): project concluded
**Did:** merged the combined dependency update #28 (closed Dependabot #23–#27; ruff pins kept in step), released v1.1.1, and marked the project complete at the user's request: README status, this board ("Possible future work" instead of a plan), and the oldest handoff archived. No new testing was done in this session, as the user asked.

**Next:** nothing planned. Expect only Dependabot updates: combine them into one PR and keep the ruff version identical in `pyproject.toml`, `.pre-commit-config.yaml` and `ci.yml`.

**Watch out:** the GPU on the dev machine is shared with the user's other jobs; check `nvidia-smi` before any real try-on, and never stop processes you didn't start.

### 2026-10-24 · Claude Code (Opus 5.5): v1.1.0
**Did:** with the user's approval of BiRefNet and Playwright (Docker and the tag report skipped; no personal wardrobe photos), shipped six PRs, all merged with CI green:
- #16 garment cleaning: BiRefNet on CPU because its GPU arena starved try-on (ADR-011)
- #17 start scripts: found and fixed native exit codes being ignored and a locked-exe reinstall
- #18 saved looks (SQLite + PNG), with a sticky-column layout fix
- #19 your own garments: `upload-` prefix, looks keyed by filename with a DB migration (ADR-012)
- #20 Playwright e2e with a fake-model server, plus an `e2e` CI job and real screenshots via `npm run screenshots`
- #21 combined dependency updates (closed Dependabot #10–#15), `npm audit` clean
Then released v1.1.0. Tests: 63 pytest, 19 Vitest, 4 Playwright.

**Next:** nothing planned; see "Later".

**Watch out:** fast tests must never hit real `artifacts/` (inject `LookStore`, `index_dir` and `tag_rows`, and force `garment.weights_ready()` to False); this bit us twice. Item ids shift when uploads are deleted; store filenames. Keep the ruff pin identical in pyproject, pre-commit and ci.yml.
