"""Virtual try-on with FASHN VTON v1.5 (optional extra: ``pip install -e ".[tryon]"``).

Kept separate from ``core.py`` because it is a different, much larger model (~2 GB of
weights, ~8 GB VRAM) that is only loaded when someone actually asks for a try-on.
"""

import importlib.util
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Literal

from PIL import Image

from .config import TRYON_WEIGHTS_DIR

FashnCategory = Literal["tops", "bottoms", "one-pieces"]
GarmentPhotoType = Literal["flat-lay", "model"]

TRYON_REPO = "fashn-ai/fashn-vton-1.5"
DWPOSE_REPO = "fashn-ai/DWPose"
DWPOSE_FILES = ["yolox_l.onnx", "dw-ll_ucoco_384.onnx"]
MIN_FREE_VRAM_GB = 5.0  # measured peak ~4.4 GB torch + ONNX pose/parser on RTX 4060

INSTALL_HINT = (
    "Virtual try-on needs the optional extra and its weights (~2 GB):\n"
    '  pip install -e ".[tryon]"\n'
    "  fashion-search tryon-download"
)


def is_installed() -> bool:
    return importlib.util.find_spec("fashn_vton") is not None


def weights_ready(weights_dir: Path = TRYON_WEIGHTS_DIR) -> bool:
    return (weights_dir / "model.safetensors").exists() and all(
        (weights_dir / "dwpose" / f).exists() for f in DWPOSE_FILES
    )


def is_available(weights_dir: Path = TRYON_WEIGHTS_DIR) -> bool:
    return is_installed() and weights_ready(weights_dir)


def fashn_category(category_tag: str) -> FashnCategory:
    """Map one of our taxonomy categories to FASHN's three garment categories."""
    return "one-pieces" if category_tag == "dress" else "tops"


def download_weights(weights_dir: Path = TRYON_WEIGHTS_DIR) -> None:
    """Fetch the try-on model, DWPose and the human parser (same sources as FASHN's script)."""
    from huggingface_hub import hf_hub_download

    weights_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {TRYON_REPO} weights to {weights_dir} ...")
    hf_hub_download(TRYON_REPO, "model.safetensors", local_dir=weights_dir)
    for name in DWPOSE_FILES:
        hf_hub_download(DWPOSE_REPO, name, local_dir=weights_dir / "dwpose")
    print("Caching the human parser (Hugging Face cache) ...")
    from fashn_human_parser import FashnHumanParser

    FashnHumanParser(device="cpu")
    print("Done.")


def low_vram_warning(min_free_gb: float = MIN_FREE_VRAM_GB) -> str | None:
    """A warning if the GPU is too full for try-on, else None.

    On Windows the driver silently spills into system RAM instead of failing, which makes
    a ~1 min try-on take 10+ min, so warn before loading rather than after.
    """
    import torch

    if not torch.cuda.is_available():
        return "No CUDA GPU found: try-on will run on CPU and take many minutes."
    free, _ = torch.cuda.mem_get_info()
    if free / 2**30 < min_free_gb:
        return (
            f"Only {free / 2**30:.1f} GB of GPU memory is free "
            f"(try-on needs ~{min_free_gb:.0f} GB). "
            "Another process is probably using the GPU; try-on will be very slow."
        )
    return None


@lru_cache(maxsize=1)
def load_pipeline(weights_dir: Path = TRYON_WEIGHTS_DIR):
    if not is_available(weights_dir):
        raise RuntimeError(INSTALL_HINT)
    if warning := low_vram_warning():
        warnings.warn(warning, stacklevel=2)
    from fashn_vton import TryOnPipeline

    return TryOnPipeline(weights_dir=str(weights_dir))


def try_on(
    person: Image.Image,
    garment: Image.Image,
    category: FashnCategory = "tops",
    garment_photo_type: GarmentPhotoType = "model",
    steps: int = 30,
    seed: int = 42,
) -> Image.Image:
    """Return a photo of ``person`` wearing ``garment``."""
    result = load_pipeline()(
        person_image=person.convert("RGB"),
        garment_image=garment.convert("RGB"),
        category=category,
        garment_photo_type=garment_photo_type,
        num_timesteps=int(steps),
        seed=int(seed),
    )
    return result.images[0]
