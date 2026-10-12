# Progress & Handoff

Read the **Now** section and the latest handoff entries at the start of every session.
Update both at the end (see `AGENTS.md` → Session protocol).

## Status

**Version:** 0.1.0 · **Milestone:** v0.2 virtual try-on · **Health:** green (search app works, tests pass)

## Task board

### Now
- _(nothing in progress)_

### Next: v0.2 virtual try-on
- [ ] Check that FASHN VTON v1.5 fits in 8 GB VRAM at fp16 (official repo and model card; confirm the licence is Apache-2.0)
- [ ] `src/fashion_search/tryon.py`: lazy model load, `try_on(person_img, garment_img) -> PIL.Image`
- [ ] Replace the placeholder "Virtual try-on" tab: upload a person photo, pick a garment from search results, show the output
- [ ] Slow test for try-on and an ADR for the model choice

### Later
- [ ] Tag accuracy check: hand-label about 50 photos and report per-attribute accuracy in `reports/`
- [ ] Combined search (text query + tag filters together)
- [ ] Larger catalogue: a properly licensed dataset (e.g. DeepFashion or Fashionpedia, licence permitting)
- [ ] Dockerfile and a deployment option (Hugging Face Spaces)

### Done
- [x] v0.1.0: zero-shot tagging, text/image search, tag browser, old-vs-new evaluation
- [x] Professional repo setup: package, CLI, tests, CI, docs system, templates

## Known issues
- The "Virtual try-on" tab is a placeholder.
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
