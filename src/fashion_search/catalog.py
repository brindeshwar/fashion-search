"""The searchable catalogue: embeddings + tag table. Pure numpy/pandas, no model needed."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .taxonomy import ATTRIBUTES

EMBEDDINGS_FILE = "embeddings.npy"
CATALOG_FILE = "catalog.csv"


@dataclass
class Catalog:
    embeddings: np.ndarray  # (N, D), L2-normalised
    table: pd.DataFrame  # one row per image: file + one column per attribute
    image_dir: Path

    @classmethod
    def load(cls, index_dir: Path, image_dir: Path) -> "Catalog":
        if not (index_dir / EMBEDDINGS_FILE).exists():
            raise FileNotFoundError(f"No index in {index_dir}. Run `fashion-search index` first.")
        return cls(
            embeddings=np.load(index_dir / EMBEDDINGS_FILE),
            table=pd.read_csv(index_dir / CATALOG_FILE),
            image_dir=image_dir,
        )

    def save(self, index_dir: Path) -> None:
        index_dir.mkdir(parents=True, exist_ok=True)
        np.save(index_dir / EMBEDDINGS_FILE, self.embeddings)
        self.table.to_csv(index_dir / CATALOG_FILE, index=False)

    def __len__(self) -> int:
        return len(self.table)

    def path(self, i: int) -> str:
        return str(self.image_dir / self.table.file.iloc[i])

    def top_k(self, query_emb: np.ndarray, k: int) -> list[tuple[int, float]]:
        """Indices and cosine scores of the k items most similar to the query."""
        scores = self.embeddings @ query_emb
        best = np.argsort(-scores)[:k]
        return [(int(i), float(scores[i])) for i in best]

    def filter(self, **tags: str) -> np.ndarray:
        """Indices of items matching every given tag. Values of None or 'any' are ignored."""
        mask = np.ones(len(self), bool)
        for attr, value in tags.items():
            if attr not in ATTRIBUTES:
                raise KeyError(f"Unknown attribute: {attr}")
            if value and value != "any":
                mask &= (self.table[attr] == value).to_numpy()
        return np.flatnonzero(mask)
