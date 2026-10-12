"""Build the catalogue index: embed every image and zero-shot tag it."""

import time
from pathlib import Path

import pandas as pd

from .catalog import Catalog
from .config import IMAGE_EXTENSIONS
from .core import DEVICE, embed_images, tag_images


def build_index(data_dir: Path, index_dir: Path) -> Catalog:
    paths = sorted(p for p in data_dir.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)
    if not paths:
        raise FileNotFoundError(f"No images found in {data_dir}")
    print(f"Embedding {len(paths)} images on {DEVICE}...")
    t0 = time.time()
    emb = embed_images(paths)
    print(f"  done in {time.time() - t0:.1f}s, shape {emb.shape}")

    rows = [{"file": p.name} for p in paths]
    for attr, (labels, probs) in tag_images(emb).items():
        best = probs.argmax(1)
        for row, b, p in zip(rows, best, probs, strict=True):
            row[attr] = labels[b]
            row[f"{attr}_conf"] = round(float(p[b]), 3)

    catalog = Catalog(emb, pd.DataFrame(rows), data_dir)
    catalog.save(index_dir)
    print(f"Saved index to {index_dir}")
    return catalog
