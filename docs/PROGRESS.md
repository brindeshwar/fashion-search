# Progress and handoff

Read **Status**, **Now** and the latest handoff entry at the start of every session, and
update them at the end (see `AGENTS.md` → Session protocol). Keep this file short: when the
handoff log grows past about three entries, move the older ones to `docs/history/`.

## Status

**Version:** 1.0.0 · **Health:** green: search, tagging, try-on and the web app are verified
end to end on the RTX 4060; all checks pass.

## Task board

### Now
- _(nothing in progress)_

### Next (ideas, ranked)
- [ ] **Screenshot of a finished try-on** (before/after view) for the README and user guide. It was skipped for v1.0.0 because the GPU was busy with another job.
- [ ] **Cleaner garments before try-on:** remove the background and crop busy listing photos (text, props, beds). This is the biggest quality gap; see the user guide's limitations.
- [ ] **Bring your own wardrobe:** upload and delete garments from the web app, with incremental indexing.
- [ ] **Persist looks and jobs** (SQLite) so they survive a server restart.
- [ ] **One-command start and Docker** (GPU image).
- [ ] **Browser end-to-end test** (Playwright: search → pick → try on, with a fake model) in CI.
- [ ] **Tag accuracy report:** hand-label about 50 photos and publish per-tag accuracy in `reports/`.
- [ ] **Licensed demo catalogue,** which would allow unblurred screenshots and a public demo.

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
