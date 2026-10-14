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
