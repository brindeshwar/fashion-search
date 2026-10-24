# Handoff log: October 2026

Handoff entries moved from `docs/PROGRESS.md` when v1.0.0 was prepared. Newest first,
unchanged from when they were written; they describe the state at the time.

### 2026-10-13 · Claude Code (Opus 5.5): v0.3 web app
**Did:** fixed ORT on CPU (ADR-008) and opened PR #3 (CI green; merging was blocked by auto mode, so the user must merge). The user picked design 5, "Virtual mirror". Built a FastAPI backend and a React frontend (ADR-009), checked end to end in the browser on the real GPU, and fixed two bugs found while testing (the compare slider started fully on "before", and a false low-VRAM warning came from our own loaded model).

**Next:** the user merges PR #3. Then open the v0.3 PR from `feat/web-app` and tag both releases. After that: tag accuracy check, background removal before try-on, Docker.

**Watch out:** `feat/web-app` is branched from `feat/virtual-try-on`, so if PR #3 is squash-merged, rebase `feat/web-app` onto main first. Keep `web/src/lib/api.ts` in sync with `api.py`.

### 2026-10-13 · Claude Code (Opus 5.5): try-on verification
**Did:** installed `[tryon]` (user approved) and downloaded the weights. The first run crawled because another user job (`medsignal.baselines.encoder`) held 7.4 GB of the GPU; waited for it to finish (didn't kill it). Verified: 49 s/image, 4.4 GB peak. Ran an ablation (sheets in `artifacts/tryon_test/`, git-ignored), switched the default photo type to "model", and added `low_vram_warning`. 29 fast tests pass.

**Next:** `pytest -m slow`, then with the user's OK push `feat/virtual-try-on`, open a PR, merge, tag v0.2.0.

**Watch out:** never kill GPU processes that aren't ours. Check `nvidia-smi` before long GPU runs.

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
