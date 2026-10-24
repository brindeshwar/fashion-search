# Setup

Commands are for Windows (PowerShell or Git Bash). On Linux or macOS, replace
`.venv/Scripts/` with `.venv/bin/`.

## Requirements

| | Minimum | Recommended |
|---|---|---|
| Python | 3.10 | 3.12 |
| Node.js (to build the web app) | 20 | 24 |
| GPU | none (CPU works for search) | NVIDIA with 8 GB VRAM for try-on |
| Disk | ~3 GB (search model + environment) | ~6 GB with try-on weights |

## Quick start

`start.ps1` (Windows) and `start.sh` (Linux/macOS) do steps 1–3 below for you, skipping
anything that's already done, and then start the server:

```bash
.\start.ps1                   # search and web app
.\start.ps1 -WithTryOn        # also install try-on and its weights (~3.2 GB)
.\start.ps1 -Port 9000        # another port
.\start.ps1 -SetupOnly        # set everything up, don't start the server
```

On Linux/macOS: `./start.sh`, `--with-tryon`, `--port 9000`, `--setup-only`. The script picks
the CUDA or CPU build of PyTorch depending on whether `nvidia-smi` is present. It refuses to
run if the port is already in use, because a running server locks files that a reinstall needs.

The manual steps follow.

## 1. Install

```bash
git clone https://github.com/brindeshwar/fashion-search.git
cd fashion-search
python -m venv .venv

# PyTorch first, matched to your hardware:
.venv/Scripts/python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126   # NVIDIA GPU
# .venv/Scripts/python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu  # CPU only

.venv/Scripts/python -m pip install -e .
```

The first run downloads the Marqo-FashionSigLIP model (~800 MB) into the Hugging Face cache
(`~/.cache/huggingface`).

## 2. Add your wardrobe

Put garment photos (JPG, PNG or WEBP) in `data/shirts/`, or anywhere else and pass
`--data-dir`. See [`data/README.md`](../data/README.md). Then build the index:

```bash
.venv/Scripts/fashion-search index
```

This embeds and tags every photo (about 20 s for 500 photos on a GPU) and writes
`artifacts/index/`. Rerun it whenever you add or remove photos.

## 3. Build and start the web app

```bash
npm --prefix web ci
npm --prefix web run build
.venv/Scripts/fashion-search serve
```

Open **http://127.0.0.1:8000**. `serve` takes `--host`, `--port`, `--data-dir` and `--index-dir`.
It binds to localhost only by default, because the API has no authentication.

## Virtual try-on (optional)

Try-on needs an NVIDIA GPU with about 8 GB VRAM, and about 3.2 GB of downloads.

```bash
.venv/Scripts/python -m pip install -e ".[tryon]"
.venv/Scripts/fashion-search tryon-download
```

The weights go to `artifacts/weights/fashn-vton-1.5/`, the human parser to the
Hugging Face cache, and the BiRefNet garment-cleaning model (~930 MB, MIT licence) to
`artifacts/weights/birefnet/`. Restart `serve`; the status pill should say "try-on ready".

You can also run a try-on from the command line:

```bash
.venv/Scripts/fashion-search tryon --person me.jpg --garment data/shirts/shirt.jpg --out result.png
```

**Licence note:** the try-on model is Apache-2.0, but its human-parser component is
licensed for **non-commercial use only** (NVIDIA SegFormer licence). See ADR-007 in
[DECISIONS.md](DECISIONS.md).

## Configuration

Every path can be changed with an environment variable (see `src/fashion_search/config.py`):

| Variable | Default | What it is |
|---|---|---|
| `FASHION_DATA_DIR` | `data/shirts` | Garment photos |
| `FASHION_INDEX_DIR` | `artifacts/index` | Generated embeddings and tags |
| `FASHION_TRYON_WEIGHTS_DIR` | `artifacts/weights/fashn-vton-1.5` | Try-on weights |
| `FASHION_BIREFNET_PATH` | `artifacts/weights/birefnet/BiRefNet-general-epoch_244.onnx` | Garment-cleaning model |
| `FASHION_DB_PATH` | `artifacts/mirror.db` | Saved looks (SQLite) |
| `FASHION_LOOKS_DIR` | `artifacts/looks` | Saved look images |
| `FASHION_CLEANED_DIR` | `artifacts/cleaned` | Cache of cleaned garment photos |
| `FASHION_MNIST_DIR` | `data/fashion_mnist` | Dataset for `fashion-search evaluate` |
| `FASHION_REPORTS_DIR` | `reports` | Where `evaluate` writes results |
| `FASHION_MODEL_ID` | `hf-hub:Marqo/marqo-fashionSigLIP` | Search and tagging model |
| `HF_HOME` | `~/.cache/huggingface` | Hugging Face cache (standard variable) |

## Troubleshooting

| Problem | Cause and fix |
|---|---|
| `No index in artifacts/index. Run fashion-search index first.` | Build the index (step 2). |
| The page at :8000 shows `{"detail":"Not Found"}` | The frontend isn't built. Run `npm --prefix web run build`, then restart `serve`. |
| "search only" in the app | The `[tryon]` extra or its weights are missing. Follow the try-on section above. |
| Try-on takes 10+ minutes, or a yellow GPU banner appears | Another program is using GPU memory. On Windows the driver then spills into system RAM, which is very slow. Check with `nvidia-smi`, then close or wait for the other program. |
| Log shows `Failed to create CUDAExecutionProvider` / `cublasLt64_13.dll missing` | onnxruntime-gpu 1.27+ needs CUDA 13, but PyTorch here uses CUDA 12. Reinstall the extra, which pins a CUDA 12 build: `pip install -e ".[tryon]"` (ADR-008). Try-on still works without this, but pose detection runs on the CPU. |
| Results for some garments look distorted or sleeveless | Switch **Garment photo** in Fit settings, or use a cleaner garment photo. See the [user guide](USER_GUIDE.md#known-limitations). |
| `Warning: You are sending unauthenticated requests to the HF Hub` | Harmless. Set `HF_TOKEN` only if downloads are rate-limited. |
| `CUDA out of memory` | Lower **Quality** (steps) or free GPU memory. Try-on peaks at about 4.4 GB of PyTorch memory, plus the pose and parser models. |
