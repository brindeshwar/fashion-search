# Progress & Handoff

Read the **Now** section and the latest handoff entries at the start of every session.
Update both at the end (see `AGENTS.md` → Session protocol).

## Status

**Version:** 0.2.0 (branch `feat/virtual-try-on`, not merged) · **Milestone:** v0.2 virtual try-on · **Health:** amber (try-on code done, not yet run on real weights)

## Task board

### Now: v0.2 virtual try-on (branch `feat/virtual-try-on`)
- [x] Research: FASHN VTON v1.5 needs ~8 GB VRAM in bf16. The model is Apache-2.0, but the human parser is non-commercial (ADR-007)
- [x] `tryon.py`, app tab (search → pick garment → try on), `tryon` and `tryon-download` commands, tests with a fake pipeline, docs
- [ ] **Blocked on the user:** run `pip install -e ".[tryon]"` (auto mode blocked installing code from GitHub), then `fashion-search tryon-download`
- [ ] Run a real try-on on the RTX 4060: check VRAM and speed, and look at the output quality on a few shirts
- [ ] `pytest -m slow`, then open a PR and merge to main, tag v0.2.0

### Later
- [ ] Tag accuracy check: hand-label about 50 photos and report per-attribute accuracy in `reports/`
- [ ] Combined search (text query + tag filters together)
- [ ] Larger catalogue: a properly licensed dataset (e.g. DeepFashion or Fashionpedia, licence permitting)
- [ ] Dockerfile and a deployment option (Hugging Face Spaces)

### Done
- [x] v0.1.0: zero-shot tagging, text/image search, tag browser, old-vs-new evaluation
- [x] Professional repo setup: package, CLI, tests, CI, docs system, templates

## Known issues
- Try-on hasn't been run on real weights yet: VRAM fit on 8 GB and quality are unverified.
- The tags are zero-shot and not yet measured against hand labels. Spot checks look good, but bright colours on multi-colour prints are sometimes tagged "multicolored".
- `evaluate.py` takes about 3 min and downloads Fashion-MNIST (~30 MB) on first run.

## Handoff log
Newest first. Template:
```
### YYYY-MM-DD · <agent/person>
**Did:** ...
**Next:** ...
**Watch out:** ...
```

### 2026-10-13 · Claude Code (Opus 5.5): v0.2 try-on
**Did:** researched current try-on models and chose FASHN VTON v1.5 (ADR-007; documented the non-commercial human-parser licence). Added `tryon.py`, the app tab, the CLI commands, a `[tryon]` extra pinned to commit 7c0f10a, and 9 new tests (27 fast tests pass). The app shows setup instructions when try-on isn't installed (checked in the browser).

**Next:** the user installs the extra. Then download the weights, run a real try-on and check VRAM, run the slow tests, open a PR and tag v0.2.0.

**Watch out:** auto mode refuses `pip install git+https://...`, so the user must run or approve it. VRAM is tight on 8 GB: if it runs out of memory, try `--steps 20`, or free the FashionSigLIP model first.

### 2026-10-13 · Claude Code (Opus 5.5)
**Did:**
- Reviewed the 2025 notebook (`legacy/`) and found four bugs: unnormalised validation set, no `restore_best_weights`, shirt photos never inverted, and the custom data never evaluated.
- Researched current fashion AI and chose Marqo-FashionSigLIP (ADR-001).
- Built v0.1.0: indexing (500 photos in 17 s on the RTX 4060), Gradio app, and evaluation. Results: the MLP gets 87.9% on Fashion-MNIST vs 77.5% zero-shot, but on inverted (photo-like) images it's 10.0% vs 83.3%, and the MLP labels 100% of them "Shirt".
- Restructured into a professional repo: src layout, CLI, pytest (fast and slow), ruff, pre-commit, GitHub Actions CI, issue/PR templates, and the docs system (AGENTS/CLAUDE/ARCHITECTURE/DECISIONS/PROGRESS).
- Moved `Dataset/` to `data/shirts/` (git-ignored, ADR-004) and the notebook to `legacy/`.

**Next:** v0.2 virtual try-on (task board above). The user chose "search first, try-on later".

- Published as a public repo, https://github.com/brindeshwar/fashion-search. CI is green on Python 3.10 and 3.12.

**Watch out:** CI warns that `actions/checkout@v4` and `setup-python@v5` run on deprecated Node 20. Dependabot should open bump PRs, so merge them. Ask before force-pushing, rewriting history or changing repo visibility.
