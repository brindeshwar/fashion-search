# Decision Records

Append-only. To change a decision, add a new record that says `Supersedes ADR-00X`,
and mark the old one `Superseded`. Format: context → decision → consequences.

---

## ADR-001: Replace the trained MLP with zero-shot Marqo-FashionSigLIP
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** The 2025 project trained a dense MLP on 28×28 grayscale Fashion-MNIST. It can't use colour, can't recognise new categories without retraining, and turned out to rely on a background shortcut (it labels any light-background image "Shirt"). A web survey in October 2026 found that fashion-specific CLIP/SigLIP models are now standard for classification and retrieval.
- **Alternatives:** fine-tune a CNN/ViT on the shirt photos (needs labels we don't have); generic OpenAI CLIP or SigLIP (weaker on fashion); Marqo-FashionCLIP (older and weaker than the SigLIP variant according to Marqo's own benchmarks); a hosted API (cost and lock-in).
- **Decision:** use `hf-hub:Marqo/marqo-fashionSigLIP` (Apache-2.0) through `open_clip`, zero-shot, with no training.
- **Consequences:** works on full-colour photos, the tag vocabulary is plain text in `taxonomy.py`, and the first run downloads about 800 MB. It scores lower than the MLP on raw Fashion-MNIST (77.5% vs 87.9%) but far higher on photo-like inputs (83.3% vs 10.0%).

## ADR-002: Brute-force numpy search, no vector database
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** The catalogue has 500 items × 768 dims, about 1.5 MB.
- **Decision:** keep embeddings in a `.npy` file and search with a single matrix product.
- **Consequences:** zero extra dependencies and millisecond queries. Revisit (FAISS or a vector DB) once the catalogue passes about 100k items.

## ADR-003: Gradio for the UI
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** we need image upload, a gallery and tabs quickly, in Python, on a local GPU.
- **Alternatives:** Streamlit (weaker galleries); FastAPI + React (much more code).
- **Decision:** Gradio Blocks, built by `build_app(catalog)` so it can be tested without the model.

## ADR-004: Dataset photos are not committed to git
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** `data/shirts/` holds 500 photos (106 MB) collected from second-hand marketplace listings. We don't hold the rights to redistribute them, and they would bloat the repo.
- **Decision:** git-ignore `data/` and `artifacts/`. Document in `data/README.md` how to obtain or replace the data. CI tests use fake embeddings.
- **Consequences:** a fresh clone needs its own images (any folder works via `--data-dir` or `FASHION_DATA_DIR`). Revisit if the photos are replaced with a properly licensed set.

## ADR-005: src layout, pyproject, CLI entry point
- **Date:** 2026-10-13 · **Status:** Accepted
- **Decision:** the package lives in `src/fashion_search/` and is installed editable. A single `fashion-search` CLI replaces the loose scripts. ruff handles lint and format, pytest handles tests, and slow tests are behind `-m slow`.
- **Consequences:** imports work the same from tests, the CLI and notebooks. CI stays CPU-only and fast.

## ADR-006: Shared agent instructions live in AGENTS.md
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** several coding agents (Claude Code, Codex, Cursor, Copilot, Gemini) may work on this repo, and each looks for a different file name.
- **Decision:** `AGENTS.md` is the single source of truth. `CLAUDE.md` imports it with `@AGENTS.md` and adds only Claude-specific notes. Project state lives in `docs/PROGRESS.md`, never in any one agent's private memory.

## ADR-007: FASHN VTON v1.5 for virtual try-on, as an optional extra
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** v0.2 adds "see this shirt on a person". The candidates in October 2026: FASHN VTON v1.5 (Jan 2026, Apache-2.0 model weights, maskless, ~8 GB VRAM), CatVTON and IDM-VTON (2024, non-commercial licences, older), and OpenTryOn (a toolkit wrapping several models).
- **Decision:** use FASHN VTON v1.5 through its own `TryOnPipeline`, installed as an optional `[tryon]` extra pinned to commit `7c0f10a`, because the package isn't on PyPI.
- **Licence caveat:** the try-on model and code are Apache-2.0, but the `fashn-human-parser` dependency inherits the **NVIDIA SegFormer licence (non-commercial)**. This project is non-commercial. Any commercial use must replace the parser or obtain a licence.
- **Consequences:** the base install stays light and CI never downloads it. Try-on is close to the 8 GB VRAM limit of the dev laptop (RTX 4060). If it runs out of memory, the first things to try are fewer steps or freeing FashionSigLIP before loading try-on.
