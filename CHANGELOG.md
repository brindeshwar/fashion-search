# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

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
