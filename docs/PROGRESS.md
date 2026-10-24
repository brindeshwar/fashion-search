# Progress and handoff

Read **Status**, **Now** and the latest handoff entry at the start of every session, and
update them at the end (see `AGENTS.md` → Session protocol). Keep this file short: when the
handoff log grows past about three entries, move the older ones to `docs/history/`.

## Status

**Version:** 1.0.0 · **Health:** green: search, tagging, try-on and the web app are verified
end to end on the RTX 4060; all checks pass.

## Task board

### Now: v1.1 (agreed with the user on 2026-10-24, one PR each)
- [x] **Clean garments before try-on:** BiRefNet on CPU, cached, on by default (ADR-011)
- [ ] **Persist looks and jobs** (SQLite) so they survive a server restart
- [ ] **Upload your own garments** in the web app (delete applies to uploads only), with incremental indexing
- [x] **One-command start scripts** (`start.ps1` / `start.sh`)
- [ ] **Browser end-to-end test** (Playwright, approved) in CI
- [ ] **Screenshot of a finished try-on** for the README and user guide

### Skipped by the user (2026-10-24)
- Docker image: not needed for local use; the start scripts cover it
- Tag accuracy report: maybe later
- Licensed demo catalogue from the user's own clothes: the user doesn't want to share their wardrobe

### Done
- [x] v0.1.0: zero-shot tagging, search, old-vs-new evaluation, professional repo setup
- [x] v0.2.0: virtual try-on (FASHN VTON v1.5), GPU pose fix, "model" photo-type default
- [x] v0.3.0: Mirror web app (React + FastAPI), combined search, async try-on jobs
- [x] v1.0.0: removed Gradio, reorganized docs (user, setup, API and development guides), dependency updates, releases tagged

## Known issues
- Try-on is poor on wrinkled garments photographed on beds or walls, and on listing photos with text or props.
- Try-on slows to 10+ min when another process holds the GPU (the Windows driver spills to RAM). `/api/health` warns about this.
- Tags are zero-shot and haven't been measured against hand labels. Bright colours on multi-colour prints are sometimes tagged "multicolored".
- Jobs and looks are in memory only, so a restart clears them.

## Handoff log
Newest first. Older entries: [`history/handoffs-2026-10.md`](history/handoffs-2026-10.md).

```
### YYYY-MM-DD · <agent/person>
**Did:** ...
**Next:** ...
**Watch out:** ...
```

### 2026-10-15 · Claude Code (Opus 5.5): v1.0.0 cleanup
**Did:** merged Dependabot #1, #6 and #8 and closed #7 (Node 24 types; Dependabot now ignores major `@types/node`). Removed the Gradio UI (ADR-010). Wrote USER_GUIDE, SETUP, API and DEVELOPMENT, plus a docs index; rewrote README and CONTRIBUTING; added docstrings everywhere (they also feed `/docs`). Archived old handoffs. Moved the repo from `D:\PE_project` to `D:\Projects\fashion-search` and rebuilt `.venv` and the pre-commit hook there. All checks pass: 41 pytest, 13 Vitest, ruff, oxlint, tsc, build, and links.

**Next:** the user merges the v1.0.0 PR, then tag v1.0.0. A finished-try-on screenshot is still missing (the GPU was busy).

**Watch out:** the user runs long GPU benchmarks (`medsignal`, via Ollama) on this machine; try-on crawls while they run. The empty `D:\PE_project` folder is left for the user to delete (the tools refuse to remove the session's original folder).
