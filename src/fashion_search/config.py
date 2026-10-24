"""Project paths and settings. Every path can be overridden with an environment variable."""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _path(env_var: str, default: Path) -> Path:
    return Path(os.environ.get(env_var, default))


MODEL_ID = os.environ.get("FASHION_MODEL_ID", "hf-hub:Marqo/marqo-fashionSigLIP")
DATA_DIR = _path("FASHION_DATA_DIR", REPO_ROOT / "data" / "shirts")
FASHION_MNIST_DIR = _path("FASHION_MNIST_DIR", REPO_ROOT / "data" / "fashion_mnist")
INDEX_DIR = _path("FASHION_INDEX_DIR", REPO_ROOT / "artifacts" / "index")
REPORTS_DIR = _path("FASHION_REPORTS_DIR", REPO_ROOT / "reports")
TRYON_WEIGHTS_DIR = _path(
    "FASHION_TRYON_WEIGHTS_DIR", REPO_ROOT / "artifacts" / "weights" / "fashn-vton-1.5"
)
BIREFNET_PATH = _path(
    "FASHION_BIREFNET_PATH",
    REPO_ROOT / "artifacts" / "weights" / "birefnet" / "BiRefNet-general-epoch_244.onnx",
)

CLEANED_DIR = _path("FASHION_CLEANED_DIR", REPO_ROOT / "artifacts" / "cleaned")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
