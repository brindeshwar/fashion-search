# Architecture

_Last updated: 2026-10-15 (v1.0.0)_

## Overview

```
 data/shirts/*.jpg ──► indexing.build_index ──► artifacts/index/
                         │  core.embed_images        ├─ embeddings.npy  (N×768 float32, L2-normalised)
                         │  core.tag_images          └─ catalog.csv     (file + 5 tags + 5 confidences)
                         ▼
                   Catalog.load ──► api.create_api (FastAPI) ◄──HTTP── web/ (React)
                                      ├─ text query  ─► core.embed_texts  ─┐
                                      ├─ tag filters ──────────────────────┴► Catalog.search
                                      ├─ image query ─► core.embed_images ──► Catalog.top_k
                                      └─ try-on      ─► jobs.JobQueue ─► tryon.try_on (optional)
```

Everything is one embedding space. Images and text prompts are both encoded by
FashionSigLIP into 768-dim unit vectors, so search is a dot product and tagging is a
softmax over dot products with the prompts for each attribute. No training happens anywhere.

## Modules (`src/fashion_search/`)

| Module | Responsibility | Imports torch? |
|---|---|---|
| `config.py` | Paths and model ID, each overridable with `FASHION_*` env vars | no |
| `taxonomy.py` | `ATTRIBUTES`: the tag vocabulary and prompt templates | no |
| `core.py` | Loads the model (cached, one per process), `embed_images`, `embed_texts`, `softmax_scores`, `zero_shot`, `tag_images` | **yes** (the only module that does) |
| `catalog.py` | `Catalog` dataclass: load/save the index, `top_k`, `filter`, `search` (filter then rank, optionally uploads only), `tag_values`, `path`; `add`/`remove`/`index_of`/`is_upload` for garments added from the app | no |
| `indexing.py` | `build_index(data_dir, index_dir)`: embeds, tags and saves; `tag_rows(emb)` (shared with uploads) | via core |
| `evaluate.py` | Old MLP vs zero-shot comparison; writes `reports/results.md` | yes |
| `tryon.py` | Optional FASHN VTON v1.5 wrapper: `is_available`, `download_weights`, `load_pipeline` (cached, lazy), `try_on`, `fashn_category` | lazily (via `fashn_vton`) |
| `garment.py` | Garment cleaning before try-on: BiRefNet (official ONNX export, run with onnxruntime-gpu) predicts a foreground mask; `composite_and_crop` (pure NumPy/PIL) puts the garment on white and crops to it with a margin, returning the photo unchanged if the mask is empty | no (ONNX Runtime, imports torch only to load CUDA DLLs) |
| `jobs.py` | `JobQueue`: one worker thread, in-memory jobs (queued, running, done or error), queue position; the job function receives its `Job`, so it can save results under the job id | no |
| `store.py` | `LookStore`: saved looks. SQLite (`artifacts/mirror.db`, table `looks`) holds metadata, and each result is a PNG in `artifacts/looks/<id>.png`. One short-lived connection per operation, so it's safe from the API and the worker thread. Also gives the median duration for progress estimates after a restart | no |
| `api.py` | FastAPI app (`create_api`) for the React UI: items (text + tags combined), image search, images, try-on jobs; also serves `web/dist` | lazily (embed functions are injectable for tests) |
| `cli.py` | `fashion-search {index,serve,evaluate,tryon,tryon-download}`; heavy imports are deferred | no |

## Invariants

1. Embeddings are always L2-normalised, so cosine similarity is just the dot product. `Catalog.top_k` depends on this.
2. Row `i` of `embeddings.npy` matches row `i` of `catalog.csv`. Both are written together by `Catalog.save`, so never edit one without the other.
3. `catalog.csv` has one column per key in `ATTRIBUTES`, plus `<attr>_conf`. If you change the taxonomy, rebuild the index.
4. Image paths are stored as bare filenames and resolved against `data_dir` at load time, so the index survives the repo being moved.
5. Item ids are row positions. Deleting an uploaded garment shifts later rows, so anything stored long-term (saved looks) refers to a garment by **filename**, never by id (ADR-012).
6. A filename starting with `upload-` marks a garment the user added. Only those can be deleted, and the marker survives a full re-index because it's part of the filename.

## Evaluation (`evaluate.py`)

- **Baseline:** the 2025 notebook's MLP (784→100→70→50→20→10). It's retrained on Fashion-MNIST plus 400 shirt photos, with two bugs from the notebook fixed: the validation set is now normalised, and the best weights are restored.
- **New:** FashionSigLIP zero-shot with the prompts `"a photo of a {class}"`.
- **Test sets:** the Fashion-MNIST test set (both raw and colour-inverted), plus 100 held-out shirt photos (`SEED = 0`).
- The inverted test set is what exposes the baseline's shortcut: it learned "light background = shirt". See `reports/results.md`.

## Virtual try-on (v0.2, optional)

```
 person photo ─┐
               ├─► tryon.try_on ─► garment.clean_garment (BiRefNet, optional) ─► fashn_vton.TryOnPipeline ─► result image
 garment ──────┘     (category: tops | bottoms | one-pieces, garment photo: flat-lay | model)
   └─ a catalogue item or an upload (POST /api/tryon), or a file (`fashion-search tryon`)
```

- Installed with the `[tryon]` extra, which pins `fashn-vton` to a git commit. Weights (~2 GB) go to `artifacts/weights/fashn-vton-1.5/` via `fashion-search tryon-download`. The human parser goes to the Hugging Face cache.
- **Invariant:** nothing imports `fashn_vton` unless try-on is actually used. The API checks `tryon.is_available()`: `/api/health` reports it, and `POST /api/tryon` returns 503 with setup instructions when it's missing, so the base install, the fast tests and CI never need it.
- `fashn_category()` maps our taxonomy to FASHN's categories (`dress` → `one-pieces`, everything else → `tops`).
- VRAM: about 8 GB for 768×1024 output in bf16 (RTX 30/40). FashionSigLIP adds about 0.8 GB if both are loaded.

## Web app (v0.3)

```
 browser (React, web/) --HTTP--> FastAPI (api.py)  -- one process: `fashion-search serve` on :8000
   Mirror + FitBar               GET  /api/health, /api/tags
   Wardrobe                      GET  /api/items?q=&color=&pattern=&sleeve=&category=&style=&uploaded=&limit=
                                 POST /api/items (add your garment); DELETE /api/items/{id} (uploads only)
                                 POST /api/items/search-by-image        (multipart image)
                                 GET  /images/{file}                    (catalogue files only)
                                 POST /api/tryon -> 202 {job}           (person file + garment_id)
                                 GET  /api/tryon/{id}  (poll ~1 s)  ->  saved as a look (store.py)
                                 GET  /api/looks, /api/looks/{id}/image; DELETE /api/looks/{id}
                                 GET  /*  -> web/dist (built SPA)
```

- **Frontend layout (`web/src/`):** `App.tsx` (state: person photo, chosen garment, fit settings, session looks), `components/Mirror.tsx` (empty -> photo -> fitting overlay -> before/after `CompareSlider`), `FitBar.tsx` (garment and settings), `Wardrobe.tsx` (search, photo search, filters, grid), `hooks/useTryOn.ts` (submit + poll; `run()` resolves with the finished job), `lib/api.ts` (typed client; **keep it in sync with the pydantic models in `api.py`**).
- **Dev loop:** `fashion-search serve` (API on :8000) plus `npm --prefix web run dev` (Vite on :5173, which proxies `/api` and `/images` to :8000).
- **Progress:** the server reports `elapsed_seconds` and `expected_seconds` (median of past runs, default 55 s). The client interpolates between polls and caps the bar at 97% until the job is done.
- **Security:** `/images/{file}` serves only filenames that are in the catalogue (no path traversal). Uploads are capped at 15 MB and must decode as images. There's no auth, so the server binds to 127.0.0.1.

## Repository layout

```
src/fashion_search/   Python package (modules above)
web/                  React frontend: src/{App.tsx, components/, hooks/, lib/}, built to web/dist/
tests/                pytest: conftest (fake catalogue), test_api, test_catalog, test_cli, test_core, test_tryon
docs/                 guides, ADRs, progress; history/ (old handoffs), images/ (screenshots)
reports/              generated evaluation output (results.md)
legacy/               the original 2025 notebook (read-only)
data/  artifacts/     local, git-ignored: photos, Fashion-MNIST, index, try-on weights
start.ps1, start.sh   one-command setup + serve
```
