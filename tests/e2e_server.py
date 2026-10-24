"""The real API and web app with fake models, for the Playwright end-to-end tests.

Serves the built frontend (`web/dist`) and the real FastAPI routes on a tiny generated
catalogue. Search, tagging and try-on are instant fakes, so the browser tests run anywhere
(including CI on CPU) in seconds and never touch the real index or saved looks.

Run: python tests/e2e_server.py [port]   (the Playwright config starts it for you)
"""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import uvicorn
from PIL import Image, ImageDraw

from fashion_search import garment, tryon
from fashion_search.api import create_api
from fashion_search.catalog import Catalog
from fashion_search.store import LookStore

GARMENTS = [  # file, colour (RGB), tags
    ("red-plaid.jpg", (190, 40, 40), "button-up shirt", "red", "checked plaid", "long sleeves"),
    ("navy-denim.jpg", (40, 60, 120), "button-up shirt", "navy", "denim", "short sleeves"),
    (
        "white-formal.jpg",
        (235, 235, 235),
        "button-up shirt",
        "white",
        "plain solid-color",
        "long sleeves",
    ),
    ("green-stripe.jpg", (40, 140, 80), "polo shirt", "green", "striped", "short sleeves"),
    ("pink-floral.jpg", (230, 140, 170), "blouse", "pink", "floral", "short sleeves"),
    ("black-tee.jpg", (30, 30, 30), "t-shirt", "black", "graphic print", "short sleeves"),
]
DIM = 16


def garment_photo(color: tuple[int, int, int]) -> Image.Image:
    """A simple shirt silhouette so screenshots and the UI look plausible."""
    img = Image.new("RGB", (300, 400), (245, 245, 240))
    d = ImageDraw.Draw(img)
    d.polygon(
        [(70, 80), (230, 80), (280, 150), (240, 170), (230, 360), (70, 360), (60, 170), (20, 150)],
        fill=color,
    )
    d.polygon([(125, 80), (150, 115), (175, 80)], fill=(245, 245, 240))
    return img


def build(root: Path):
    image_dir = root / "shirts"
    image_dir.mkdir()
    rows, emb = [], np.eye(len(GARMENTS), DIM, dtype=np.float32)
    for file, rgb, category, color, pattern, sleeve in GARMENTS:
        garment_photo(rgb).save(image_dir / file)
        rows.append(
            {
                "file": file,
                "category": category,
                "color": color,
                "pattern": pattern,
                "sleeve": sleeve,
                "style": "casual",
            }
        )
    catalog = Catalog(emb, pd.DataFrame(rows), image_dir)

    def embed_text(q: str) -> np.ndarray:
        # The first garment whose colour or pattern is mentioned ranks first.
        q = q.lower()
        for i, r in enumerate(rows):
            if r["color"] in q or r["pattern"].split()[-1] in q:
                return emb[i]
        return emb[0]

    def tag_rows(e: np.ndarray) -> list[dict]:
        return [
            {
                "category": "t-shirt",
                "color": "black",
                "pattern": "graphic print",
                "sleeve": "short sleeves",
                "style": "casual",
            }
            for _ in e
        ]

    def fake_try_on(person, garment_img, *args, **kwargs) -> Image.Image:
        # "Wear" the garment: paste it over the middle of the person photo.
        out = person.convert("RGB").copy()
        g = garment_img.convert("RGB").copy()
        g.thumbnail((out.width // 2, out.height // 2))
        out.paste(g, ((out.width - g.width) // 2, out.height // 4))
        return out

    tryon.is_available = lambda *a: True
    tryon.try_on = fake_try_on
    tryon.low_vram_warning = lambda *a: None
    garment.weights_ready = lambda *a: False

    return create_api(
        catalog,
        embed_text=embed_text,
        embed_image=lambda im: emb[1],
        store=LookStore(root / "mirror.db", root / "looks"),
        index_dir=root / "index",
        tag_rows=tag_rows,
    )


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    with tempfile.TemporaryDirectory() as tmp:
        uvicorn.run(build(Path(tmp)), host="127.0.0.1", port=port, log_level="warning")
