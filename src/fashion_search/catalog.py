"""The searchable catalogue: embeddings + tag table. Pure numpy/pandas, no model needed."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .taxonomy import ATTRIBUTES

EMBEDDINGS_FILE = "embeddings.npy"
CATALOG_FILE = "catalog.csv"
# Garments added from the web app are saved as "upload-<id>.jpg" in the image folder. The
# prefix marks them as the user's own (deletable) and survives a full re-index.
UPLOAD_PREFIX = "upload-"


@dataclass
class Catalog:
    """Embeddings and tags for every catalogue photo; row i of each belongs together."""

    embeddings: np.ndarray  # (N, D), L2-normalised
    table: pd.DataFrame  # one row per image: file + one column per attribute
    image_dir: Path

    @classmethod
    def load(cls, index_dir: Path, image_dir: Path) -> "Catalog":
        """Load an index written by `fashion-search index`."""
        if not (index_dir / EMBEDDINGS_FILE).exists():
            raise FileNotFoundError(f"No index in {index_dir}. Run `fashion-search index` first.")
        return cls(
            embeddings=np.load(index_dir / EMBEDDINGS_FILE),
            table=pd.read_csv(index_dir / CATALOG_FILE),
            image_dir=image_dir,
        )

    def save(self, index_dir: Path) -> None:
        """Write embeddings and tags together, keeping their rows aligned."""
        index_dir.mkdir(parents=True, exist_ok=True)
        np.save(index_dir / EMBEDDINGS_FILE, self.embeddings)
        self.table.to_csv(index_dir / CATALOG_FILE, index=False)

    def __len__(self) -> int:
        return len(self.table)

    def path(self, i: int) -> str:
        """Absolute path of the photo for row `i`."""
        return str(self.image_dir / self.table.file.iloc[i])

    def top_k(self, query_emb: np.ndarray, k: int) -> list[tuple[int, float]]:
        """Indices and cosine scores of the k items most similar to the query."""
        scores = self.embeddings @ query_emb
        best = np.argsort(-scores)[:k]
        return [(int(i), float(scores[i])) for i in best]

    def filter(self, uploads_only: bool = False, **tags: str) -> np.ndarray:
        """Indices of items matching every given tag. Values of None or 'any' are ignored."""
        mask = np.ones(len(self), bool)
        if uploads_only:
            mask &= self.table.file.astype(str).str.startswith(UPLOAD_PREFIX).to_numpy()
        for attr, value in tags.items():
            if attr not in ATTRIBUTES:
                raise KeyError(f"Unknown attribute: {attr}")
            if value and value != "any":
                mask &= (self.table[attr] == value).to_numpy()
        return np.flatnonzero(mask)

    def search(
        self,
        query_emb: np.ndarray | None = None,
        k: int = 50,
        uploads_only: bool = False,
        **tags: str,
    ) -> list[tuple[int, float | None]]:
        """Filter by tags, then rank by similarity to the query (catalogue order if no query)."""
        idx = self.filter(uploads_only, **tags)
        if query_emb is None:
            return [(int(i), None) for i in idx[:k]]
        scores = self.embeddings[idx] @ query_emb
        order = np.argsort(-scores)[:k]
        return [(int(idx[o]), float(scores[o])) for o in order]

    def tag_values(self) -> dict[str, list[str]]:
        """Tag values that actually occur in the catalogue, per attribute."""
        return {attr: sorted(self.table[attr].unique()) for attr in ATTRIBUTES}

    def index_of(self, file: str) -> int | None:
        """Row of the photo with this filename, or None."""
        hits = np.flatnonzero(self.table.file.to_numpy() == file)
        return int(hits[0]) if len(hits) else None

    def is_upload(self, i: int) -> bool:
        """Whether row `i` is a garment the user added (and may delete)."""
        return str(self.table.file.iloc[i]).startswith(UPLOAD_PREFIX)

    def add(self, file: str, embedding: np.ndarray, tags: dict) -> int:
        """Append a photo with its embedding and tags; returns its row."""
        row = pd.DataFrame([{"file": file} | tags], columns=self.table.columns)
        # Replace (not mutate) the arrays so concurrent readers see a consistent pair.
        self.table = pd.concat([self.table, row], ignore_index=True)
        self.embeddings = np.vstack([self.embeddings, embedding[None].astype(np.float32)])
        return len(self) - 1

    def remove(self, i: int) -> str:
        """Drop row `i` (later rows shift up by one); returns the removed filename."""
        file = str(self.table.file.iloc[i])
        self.table = self.table.drop(index=i).reset_index(drop=True)
        self.embeddings = np.delete(self.embeddings, i, axis=0)
        return file
