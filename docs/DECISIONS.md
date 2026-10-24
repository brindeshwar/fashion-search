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
- **Date:** 2026-10-13 · **Status:** Superseded by ADR-010
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

## ADR-008: Try-on defaults: "model" photo type, onnxruntime-gpu < 1.27
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** On our catalogue (shirts on hangers, beds and walls, often with listing text), FASHN's "flat-lay" mode turned long-sleeve shirts sleeveless and copied text and background into the garment. Separately, onnxruntime-gpu 1.27+ is built for CUDA 13, but our torch uses CUDA 12.6, so pose detection silently fell back to the CPU.
- **Evidence:** a 6-garment comparison (flat-lay vs model, `segmentation_free` on/off): "model" was clearly better on 3 of 5 catalogue shirts and similar on 1; every setting failed on wrinkled bed-photographed shirts. `segmentation_free` made little difference, so it stays at FASHN's default (True).
- **Decision:** default `garment_photo_type="model"` in the API, CLI and UI (users can still switch it). Pin `onnxruntime-gpu>=1.20,<1.27` in the `[tryon]` extra.
- **Consequences:** better default results. Revisit the ORT pin when torch moves to CUDA 13.

## ADR-009: Web app = React (Vite + TypeScript) + FastAPI, "Virtual mirror" design
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** The user found the Gradio UI weak and wanted a proper frontend. They chose design 5 of 5 ("Virtual mirror": your photo is the hero, with the wardrobe beside it).
- **Backend alternatives:** FastAPI (same Python process as the models, async, typed, OpenAPI docs); Flask (no typing or validation); Node/Express + a Python model service (two runtimes, IPC); Django (too heavy).
- **Decision:**
  - **FastAPI** in `api.py`, reusing `Catalog`/`core`/`tryon` directly. One process serves `/api`, `/images` and the built SPA (`web/dist`).
  - **Try-on as async jobs** (`jobs.py`: one worker thread, in-memory): `POST /api/tryon` returns 202 plus a job id, and the client polls about once a second. A 50 s blocking request would hit proxy timeouts and couldn't report progress. A single worker matches one GPU.
  - **React 19 + Vite + TypeScript**, plain CSS with design tokens (no UI kit), lucide icons, Vitest and Testing Library. oxlint comes from the Vite template.
  - Gradio stays as a developer tool (`fashion-search app`).
- **Consequences:** two toolchains (Python and Node) and a CI job each. Jobs are lost on restart, which is fine locally; a deployment would need a persistent queue. The API has no auth, so it binds to 127.0.0.1 by default.

## ADR-010: Remove the Gradio UI
- **Date:** 2026-10-15 · **Status:** Accepted · **Supersedes:** ADR-003
- **Context:** Since v0.3 the React Mirror app (ADR-009) does everything the Gradio UI did (text and image search, tag filters, try-on) and more. Keeping both meant two UIs to maintain, about 30 extra dependencies, and docs that pointed people at two different ports.
- **Decision:** delete `app.py`, the `fashion-search app` command and the `gradio` dependency. `fashion-search serve` is the only UI.
- **Consequences:** smaller install and one UI to maintain. The interactive OpenAPI page at `/docs` (FastAPI) is the developer tool for poking the backend.

## ADR-011: Clean garment photos with BiRefNet on the CPU, on by default
- **Date:** 2026-10-24 · **Status:** Accepted
- **Context:** Catalogue photos show shirts on beds, walls and grass, often with price text; FASHN VTON can copy those into the result (ADR-008). The user approved adding a background-removal model.
- **Alternatives:** BRIA RMBG-2.0 (non-commercial licence); rembg (wraps the same models but needs the CPU `onnxruntime`, which conflicts with `onnxruntime-gpu`); BiRefNet via `transformers` (`trust_remote_code`); the official BiRefNet ONNX export run directly with our existing ONNX Runtime.
- **Decision:** the official `BiRefNet-general-epoch_244.onnx` (MIT, 927 MB, size-verified on download) run with ONNX Runtime **on the CPU**. The garment is placed on white and cropped with a 6% margin. Cleaned catalogue garments are cached on disk (`artifacts/cleaned/`). On by default in the API, CLI and UI (`clean_garment` / `--no-clean`).
- **Evidence (RTX 4060, 8 GB):**
  - On the GPU, BiRefNet's ONNX Runtime arena took *all* free memory (6.9 GB → 0) and failed with a 2 GB or 3 GB cap. With the try-on model resident, try-on spilled into system RAM and made no progress in 12 minutes. Released sessions return the memory, but the model can't co-exist with try-on on 8 GB.
  - On the CPU: 11–17 s per garment (6 measured), with no GPU memory used; try-on peaked at 3.6 GB of PyTorch memory with no spill.
  - Quality on 6 garments (raw vs cleaned, "model" mode): cleaning fixed 1 (striped shirt: no floor-length drape), was neutral on 4, and didn't help 1 (wrinkled shirt on a bed); it never made a result worse. With cleaned input, "flat-lay" mode was still worse on 3 of 6, so ADR-008's "model" default stands.
- **Consequences:** the first try-on of each garment takes ~15 s longer, later ones nothing extra; downloads grow by ~930 MB; ~1–2 GB of RAM is used while the model is loaded. Revisit GPU inference (or the 213 MB `swin_v1_tiny` variant) on cards with more VRAM.

## ADR-012: Your own garments: an `upload-` filename prefix, looks keyed by filename
- **Date:** 2026-10-24 · **Status:** Accepted
- **Context:** The user asked for adding their own garments from the app, with delete limited to uploads (the original 500 photos must stay safe). Item ids are row positions in the index, and saved looks referred to garments by that id.
- **Alternatives:** a separate uploads folder plus a `source` column in `catalog.csv` (a re-index would lose the column and turn uploads into undeletable catalogue items); stable integer ids (a breaking index-format change); tombstones instead of deleting rows (stale rows in every search).
- **Decision:** uploads are saved in the catalogue folder as `upload-<uuid>.jpg`; the prefix is the single source of truth for "yours" and survives a re-index. Deleting removes the row and the file, so later ids shift. Saved looks store the garment's **filename** and resolve the id when read; the looks database migrates the column in place.
- **Consequences:** no index-format change, and uploads behave like any other garment. Clients must not cache item ids across a delete (documented in API.md); the web app clears its selection after a delete.
