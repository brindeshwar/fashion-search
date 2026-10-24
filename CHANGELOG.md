# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Added
- **Add your own garments:** "Add yours" in the wardrobe uploads a photo, which is tagged and searchable immediately (`POST /api/items`), with a "Yours" filter (`uploaded=true`), badge, and delete for your uploads only (`DELETE /api/items/{id}`). ADR-012.
- **Saved looks:** every finished try-on is saved (SQLite metadata + PNG in `artifacts/`) and shows under "Your looks" after a reload or restart, with a delete button. New endpoints: `GET /api/looks`, `GET /api/looks/{id}/image`, `DELETE /api/looks/{id}`. Progress estimates use saved durations after a restart. The person photo is never stored.
- **Garment cleaning before try-on:** BiRefNet removes the garment photo's background (beds, walls, props, price text) and crops to the garment. It's on by default, with a "Clean up garment photo" toggle in Fit settings, `clean_garment` in the API and `--no-clean` in the CLI. Catalogue garments are cleaned once and cached. `fashion-search tryon-download` also fetches the model (~930 MB). See ADR-011.
- **One-command start:** `start.ps1` (Windows) and `start.sh` (Linux/macOS) set up whatever is missing (environment, optional try-on, web build, index) and start the app. Options: `-WithTryOn`, `-Port`, `-SetupOnly`.

### Fixed
- The left column (mirror, fit bar, looks) is now capped at the window height and scrolls on its own, so "Your looks" and the fit settings can't end up out of reach below a sticky column.

## [1.0.0] - 2026-10-15

### Removed
- **BREAKING:** the Gradio developer UI and the `fashion-search app` command. Use `fashion-search serve` (the Mirror web app). See ADR-010.

### Added
- Documentation set: `docs/USER_GUIDE.md`, `docs/SETUP.md`, `docs/API.md`, `docs/DEVELOPMENT.md` and a `docs/README.md` index; a rewritten README with screenshots.

### Changed
- Dependencies: TypeScript 7, `actions/checkout` v7, `actions/setup-python` v7, `actions/setup-node` v7. Dependabot ignores major `@types/node` updates so types track the Node 24 runtime.
- Older handoff entries moved from `docs/PROGRESS.md` to `docs/history/`.

## [0.3.0] - 2026-10-13

### Added
- **Mirror web app**: React + TypeScript frontend (the "Virtual mirror" design) served by a new FastAPI backend. `fashion-search serve` runs it at http://127.0.0.1:8000.
- Combined search: a text query plus tag filters in one request.
- Try-on runs as a background job with queue position and a progress estimate; before/after slider; download; a "Your looks" history for the session.
- Frontend tests (Vitest) and a `web` CI job (lint, typecheck, test, build).

### Fixed
- The low-VRAM warning no longer fires because of the app's own loaded try-on model.

## [0.2.0] - 2026-10-13

### Added
- Virtual try-on with FASHN VTON v1.5 (optional `[tryon]` extra): a new app tab that takes a person photo plus a garment found by search or uploaded.
- `fashion-search tryon` and `fashion-search tryon-download` commands.
- A warning before try-on when too little GPU memory is free.

### Changed
- Try-on defaults to the "model" garment photo type, which works much better on hanger/listing photos (ADR-008).

### Fixed
- Pose detection fell back to CPU: the `[tryon]` extra now pins `onnxruntime-gpu<1.27`, the last CUDA 12 build.

## [0.1.0] - 2026-10-13

### Added
- Zero-shot tagging (category, colour, pattern, sleeve, style) with Marqo-FashionSigLIP.
- Gradio app with text search, image search and a tag browser.
- `fashion-search` CLI with the `index`, `app` and `evaluate` commands.
- Evaluation comparing the 2025 MLP with zero-shot FashionSigLIP (`reports/results.md`).
- Tests, ruff, pre-commit, GitHub Actions CI, and issue and PR templates.
- Docs system for humans and coding agents: `AGENTS.md`, `CLAUDE.md`, `docs/`.

### Changed
- Moved the 2025 Fashion-MNIST notebook to `legacy/2025-fashion-mnist-mlp/`.
- Moved the shirt photos to `data/shirts/`. They are no longer tracked in git.

### Fixed (relative to the 2025 notebook)
- The validation set is now normalised like the training set.
- Early stopping now restores the best weights.
- The shirt photos are now evaluated on a held-out split.
