"""Clean garment photos before try-on: remove the background and crop to the garment.

Marketplace photos show shirts on beds, walls and grass, often with price text. FASHN
VTON copies those into the result (ADR-008), so try-on first cuts the garment out with
BiRefNet (MIT, official ONNX export) and places it on white, cropped with a margin.

The mask and crop logic (`composite_and_crop`) is pure NumPy/PIL so it can be tested
without the model; only `predict_mask` runs BiRefNet.

BiRefNet runs on the CPU on purpose (ADR-011): on the GPU its ONNX Runtime memory arena
needs more than 3 GB and grabs all free memory, which pushes the resident try-on model
into system RAM on an 8 GB card. On CPU it takes ~10 s, and catalogue garments are
cleaned once and cached on disk.
"""

import urllib.request
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

from .config import BIREFNET_PATH, CLEANED_DIR

BIREFNET_URL = (
    "https://github.com/ZhengPeng7/BiRefNet/releases/download/v1/BiRefNet-general-epoch_244.onnx"
)
BIREFNET_BYTES = 972_666_916  # GitHub publishes no checksum for this asset; size is checked
INPUT_SIZE = 1024
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def weights_ready(path: Path = BIREFNET_PATH) -> bool:
    """Whether the BiRefNet weights are downloaded (and complete)."""
    return path.exists() and path.stat().st_size == BIREFNET_BYTES


def download_weights(path: Path = BIREFNET_PATH) -> None:
    """Download the BiRefNet ONNX weights (~930 MB) from the official GitHub release."""
    if weights_ready(path):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(".part")
    print(f"Downloading BiRefNet (~930 MB) to {path} ...")
    urllib.request.urlretrieve(BIREFNET_URL, part)
    if part.stat().st_size != BIREFNET_BYTES:
        part.unlink()
        raise RuntimeError("BiRefNet download is incomplete; run the command again.")
    part.replace(path)


@lru_cache(maxsize=1)
def _session(path: Path = BIREFNET_PATH):
    import onnxruntime as ort

    return ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])


def predict_mask(image: Image.Image) -> np.ndarray:
    """Foreground probability per pixel (H x W, 0..1) at the image's own size."""
    rgb = image.convert("RGB")
    x = np.asarray(rgb.resize((INPUT_SIZE, INPUT_SIZE), Image.BILINEAR), dtype=np.float32)
    x = ((x / 255.0 - IMAGENET_MEAN) / IMAGENET_STD).transpose(2, 0, 1)[None]
    session = _session()
    logits = session.run(None, {session.get_inputs()[0].name: x})[-1][0, 0]
    prob = 1.0 / (1.0 + np.exp(-logits))
    mask = Image.fromarray((prob * 255).astype(np.uint8)).resize(rgb.size, Image.BILINEAR)
    return np.asarray(mask, dtype=np.float32) / 255.0


def composite_and_crop(
    image: Image.Image,
    mask: np.ndarray,
    margin: float = 0.06,
    threshold: float = 0.5,
    background: tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    """Put the masked garment on a plain background and crop to it with a small margin.

    Returns the image unchanged if the mask finds (almost) nothing, so a failed
    segmentation never makes try-on worse than the raw photo.
    """
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    alpha = np.clip(mask, 0.0, 1.0)[..., None]
    out = rgb * alpha + np.array(background, dtype=np.float32) * (1.0 - alpha)

    ys, xs = np.nonzero(mask > threshold)
    if len(ys) < 0.01 * mask.size:
        return image.convert("RGB")
    h, w = mask.shape
    pad_y, pad_x = int(margin * (ys.max() - ys.min())), int(margin * (xs.max() - xs.min()))
    top, bottom = max(0, ys.min() - pad_y), min(h, ys.max() + pad_y + 1)
    left, right = max(0, xs.min() - pad_x), min(w, xs.max() + pad_x + 1)
    return Image.fromarray(out[top:bottom, left:right].astype(np.uint8))


def clean_garment(image: Image.Image) -> Image.Image:
    """Remove the background around a garment and crop to it."""
    return composite_and_crop(image, predict_mask(image))


def clean_file(path: Path, cache_dir: Path = CLEANED_DIR) -> Image.Image:
    """Clean a garment photo from disk, caching the result so each file is cleaned once."""
    stat = path.stat()
    # Name includes size and mtime so an edited or replaced photo is cleaned again.
    cached = cache_dir / f"{path.stem}-{stat.st_size}-{int(stat.st_mtime)}.png"
    if cached.exists():
        return Image.open(cached).convert("RGB")
    cleaned = clean_garment(Image.open(path))
    cache_dir.mkdir(parents=True, exist_ok=True)
    cleaned.save(cached)
    return cleaned
