# Architecture

_Last updated: 2026-10-13 (v0.2.0)_

## Overview

```
 data/shirts/*.jpg ──► indexing.build_index ──► artifacts/index/
                         │  core.embed_images        ├─ embeddings.npy  (N×768 float32, L2-normalised)
                         │  core.tag_images          └─ catalog.csv     (file + 5 tags + 5 confidences)
                         ▼
                   Catalog.load ──► app.build_app (Gradio)
                                      ├─ text query  ─► core.embed_texts  ─► Catalog.top_k
                                      ├─ image query ─► core.embed_images ─► Catalog.top_k
                                      └─ tag filters ─────────────────────► Catalog.filter
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
| `catalog.py` | `Catalog` dataclass: load/save the index, `top_k`, `filter`, `path` | no |
| `indexing.py` | `build_index(data_dir, index_dir)`: embeds, tags and saves | via core |
| `app.py` | `build_app(catalog)` builds the Gradio Blocks; `launch()` serves it. Imports core lazily inside `build_app` | lazily |
| `evaluate.py` | Old MLP vs zero-shot comparison; writes `reports/results.md` | yes |
| `tryon.py` | Optional FASHN VTON v1.5 wrapper: `is_available`, `download_weights`, `load_pipeline` (cached, lazy), `try_on`, `fashn_category` | lazily (via `fashn_vton`) |
| `cli.py` | `fashion-search {index,app,evaluate,tryon,tryon-download}`; heavy imports are deferred | no |

## Invariants

1. Embeddings are always L2-normalised, so cosine similarity is just the dot product. `Catalog.top_k` depends on this.
2. Row `i` of `embeddings.npy` matches row `i` of `catalog.csv`. Both are written together by `Catalog.save`, so never edit one without the other.
3. `catalog.csv` has one column per key in `ATTRIBUTES`, plus `<attr>_conf`. If you change the taxonomy, rebuild the index.
4. Image paths are stored as bare filenames and resolved against `data_dir` at load time, so the index survives the repo being moved.

## Evaluation (`evaluate.py`)

- **Baseline:** the 2025 notebook's MLP (784→100→70→50→20→10). It's retrained on Fashion-MNIST plus 400 shirt photos, with two bugs from the notebook fixed: the validation set is now normalised, and the best weights are restored.
- **New:** FashionSigLIP zero-shot with the prompts `"a photo of a {class}"`.
- **Test sets:** the Fashion-MNIST test set (both raw and colour-inverted), plus 100 held-out shirt photos (`SEED = 0`).
- The inverted test set is what exposes the baseline's shortcut: it learned "light background = shirt". See `reports/results.md`.

## Virtual try-on (v0.2, optional)

```
 person photo ─┐
               ├─► tryon.try_on ─► fashn_vton.TryOnPipeline ─► result image
 garment ──────┘     (category: tops | bottoms | one-pieces, garment photo: flat-lay | model)
   └─ picked from catalogue search (app tab) or uploaded / --garment (CLI)
```

- Installed with the `[tryon]` extra, which pins `fashn-vton` to a git commit. Weights (~2 GB) go to `artifacts/weights/fashn-vton-1.5/` via `fashion-search tryon-download`. The human parser goes to the Hugging Face cache.
- **Invariant:** nothing imports `fashn_vton` unless try-on is actually used. `app.build_tryon_tab` checks `tryon.is_available()` and shows setup instructions otherwise, so the base install, the fast tests and CI never need it.
- `fashn_category()` maps our taxonomy to FASHN's categories (`dress` → `one-pieces`, everything else → `tops`).
- VRAM: about 8 GB for 768×1024 output in bf16 (RTX 30/40). FashionSigLIP adds about 0.8 GB if both are loaded.
