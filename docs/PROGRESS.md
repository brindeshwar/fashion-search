# Progress and handoff

Read **Status**, **Now** and the latest handoff entry at the start of every session, and
update them at the end (see `AGENTS.md` → Session protocol). Keep this file short: when the
handoff log grows past about three entries, move the older ones to `docs/history/`.

## Status

**Version:** 1.1.0 · **Health:** green: search, tagging, garment cleaning, try-on, saved looks,
uploads and the web app verified end to end on the RTX 4060; unit, API and browser tests pass in CI.

## Task board

### Done in v1.1 (agreed with the user on 2026-10-24, one PR each)
- [x] **Clean garments before try-on:** BiRefNet on CPU, cached, on by default (ADR-011)
- [x] **Persist looks** (SQLite + PNG files) so they survive a server restart
- [x] **Upload your own garments** in the web app (delete applies to uploads only), with incremental indexing (ADR-012)
- [x] **One-command start scripts** (`start.ps1` / `start.sh`)
- [x] **Browser end-to-end test** (Playwright) in CI, plus a screenshot script
- [x] **Screenshot of a finished try-on** for the README and user guide (no blur needed)

### Now
- _(nothing in progress)_

### Later (not planned)
- Tag accuracy report: hand-label ~50 photos and publish per-tag accuracy (the user may do this later)
- GPU garment cleaning on cards with more than 8 GB, or the 213 MB BiRefNet `swin_v1_tiny` variant (ADR-011)
- Run `start.sh` end to end on Linux/macOS (only syntax-checked so far)

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

### 2026-10-15 · Claude Code (Opus 5.5): v1.0.0 cleanup
**Did:** merged Dependabot #1, #6 and #8 and closed #7 (Node 24 types; Dependabot now ignores major `@types/node`). Removed the Gradio UI (ADR-010). Wrote USER_GUIDE, SETUP, API and DEVELOPMENT, plus a docs index; rewrote README and CONTRIBUTING; added docstrings everywhere (they also feed `/docs`). Archived old handoffs. Moved the repo from `D:\PE_project` to `D:\Projects\fashion-search` and rebuilt `.venv` and the pre-commit hook there. All checks pass: 41 pytest, 13 Vitest, ruff, oxlint, tsc, build, and links.

**Next:** the user merges the v1.0.0 PR, then tag v1.0.0. A finished-try-on screenshot is still missing (the GPU was busy).

**Watch out:** the user runs long GPU benchmarks (`medsignal`, via Ollama) on this machine; try-on crawls while they run. The empty `D:\PE_project` folder is left for the user to delete (the tools refuse to remove the session's original folder).
