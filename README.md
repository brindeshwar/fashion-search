# Fashion Visual Search

[![CI](https://github.com/brindeshwar/fashion-search/actions/workflows/ci.yml/badge.svg)](https://github.com/brindeshwar/fashion-search/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Search and auto-tag clothing photos by **text**, **image** or **attributes** using
[Marqo-FashionSigLIP](https://huggingface.co/Marqo/marqo-fashionSigLIP), a
fashion-specific vision-language model. Tagging is zero-shot, so there's no training
and no labels needed.

This is the 2026 rebuild of a 2025 Fashion-MNIST classifier, which is kept in
[`legacy/`](legacy/2025-fashion-mnist-mlp/).

## Features

| | |
|---|---|
| **Auto-tagging** | Category, colour, pattern, sleeve and style for every photo |
| **Text search** | "red and black plaid flannel" → matching items |
| **Image search** | Upload a photo → visually similar items |
| **Tag browser** | Filter the catalogue by any combination of tags |
| **Evaluation** | Old MLP vs new model, see [reports/results.md](reports/results.md) |
| **Virtual try-on** | Put any catalogue item on a photo of a person (FASHN VTON v1.5, optional) |

## Old vs new: the short version

| Test | 2025 MLP | FashionSigLIP (zero-shot) |
|---|---|---|
| Fashion-MNIST test set | **87.9%** | 77.5% |
| Same images, inverted to look like real photos | 10.0% | **83.3%** |

The old model learned "light background = shirt". The new one recognises the clothes.
The full table is in [reports/results.md](reports/results.md).

## Quickstart

Requires Python 3.10+. An NVIDIA GPU is recommended, but it also works on CPU.

```bash
git clone https://github.com/brindeshwar/fashion-search.git
cd fashion-search
python -m venv .venv
.venv/Scripts/python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
.venv/Scripts/python -m pip install -e ".[dev]"
```

Put your clothing photos in `data/shirts/` (see [data/README.md](data/README.md)), then run:

```bash
.venv/Scripts/fashion-search index
.venv/Scripts/fashion-search app
```

Then open http://localhost:7860.

**Optional: virtual try-on.** This needs an NVIDIA GPU with about 8 GB of VRAM and downloads about 2 GB.

```bash
.venv/Scripts/python -m pip install -e ".[tryon]"
.venv/Scripts/fashion-search tryon-download
.venv/Scripts/fashion-search tryon --person me.jpg --garment data/shirts/x.jpg --out out.png
```

The try-on model is Apache-2.0, but its human-parser dependency is licensed for
non-commercial use only (see [ADR-007](docs/DECISIONS.md)). On Linux or macOS, use `.venv/bin/` instead of `.venv/Scripts/`.

## Project layout

```
src/fashion_search/   package: core (model), catalog (search), indexing, app, evaluate, cli
tests/                pytest (fast by default; `-m slow` loads the real model)
docs/                 ARCHITECTURE, DECISIONS (ADRs), PROGRESS (status + handoff log)
reports/              evaluation results
legacy/               original 2025 notebook
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). AI coding agents should start with [AGENTS.md](AGENTS.md).

## License

Code: [MIT](LICENSE). FashionSigLIP is Apache-2.0 (Marqo). FASHN VTON v1.5 is Apache-2.0,
but its human parser is non-commercial (NVIDIA SegFormer licence). The photos in `data/` are not
included or licensed by this repo.
