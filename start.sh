#!/usr/bin/env bash
# One-command start for Fashion Search (Linux/macOS): sets up whatever is missing, then serves.
# Each step is skipped when its result already exists, so after the first run this just
# starts the server.
#
#   ./start.sh                 search + web app
#   ./start.sh --with-tryon    also install virtual try-on (~3.2 GB, needs an NVIDIA GPU)
#   ./start.sh --port 9000
#   ./start.sh --setup-only    set up, then exit without starting the server
set -euo pipefail
cd "$(dirname "$0")"

with_tryon=0
port=8000
setup_only=0
while [ $# -gt 0 ]; do
  case "$1" in
    --with-tryon) with_tryon=1 ;;
    --port) port="$2"; shift ;;
    --setup-only) setup_only=1 ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

step() { printf '\n==> %s\n' "$1"; }
need() { command -v "$1" >/dev/null || { echo "$1 not found. $2" >&2; exit 1; }; }

# A running server would make reinstalls fail or the new server crash on the port.
if (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null; then
  echo "Port $port is already in use. Is Mirror already running? Stop it first, or use --port." >&2
  exit 1
fi

py=.venv/bin/python
cli=.venv/bin/fashion-search

if [ ! -x "$py" ]; then
  need python3 "Install Python 3.10+."
  step "Creating Python environment (.venv)"
  python3 -m venv .venv
  "$py" -m pip install --upgrade pip
  # Pick the PyTorch build: CUDA if an NVIDIA GPU is present, otherwise CPU.
  if command -v nvidia-smi >/dev/null; then torch_index=cu126; else torch_index=cpu; fi
  step "Installing PyTorch ($torch_index)"
  "$py" -m pip install torch torchvision --index-url "https://download.pytorch.org/whl/$torch_index"
  step "Installing fashion-search"
  "$py" -m pip install -e .
fi

if [ "$with_tryon" = 1 ]; then
  ready=$("$py" -c "from fashion_search import tryon, garment; print(tryon.is_available() and garment.weights_ready())" 2>/dev/null || true)
  if [ "$ready" != True ]; then
    step "Installing virtual try-on and downloading weights (~3.2 GB)"
    "$py" -m pip install -e ".[tryon]"
    "$cli" tryon-download
  fi
fi

if [ ! -f web/dist/index.html ]; then
  need npm "Install Node.js 20+."
  step "Building the web app"
  npm --prefix web ci
  npm --prefix web run build
fi

if [ ! -f artifacts/index/embeddings.npy ]; then
  count=$(find data/shirts -maxdepth 1 -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.bmp' \) 2>/dev/null | wc -l)
  if [ "$count" -eq 0 ]; then
    echo "No garment photos found. Put JPG/PNG/WEBP photos in data/shirts/ (see data/README.md), then run this again." >&2
    exit 1
  fi
  step "Indexing $count photos"
  "$cli" index
fi

if [ "$setup_only" = 1 ]; then step "Setup complete"; exit 0; fi

step "Starting Mirror on http://127.0.0.1:$port  (Ctrl+C to stop)"
exec "$cli" serve --port "$port"
