import numpy as np
import pandas as pd
import pytest

from fashion_search.catalog import Catalog


@pytest.fixture
def catalog(tmp_path):
    """A 4-item catalogue with hand-made unit-vector embeddings (no model needed)."""
    emb = np.eye(4, 8, dtype=np.float32)
    table = pd.DataFrame(
        {
            "file": ["a.jpg", "b.jpg", "c.jpg", "d.jpg"],
            "category": ["button-up shirt"] * 3 + ["blouse"],
            "color": ["red", "blue", "red", "white"],
            "pattern": ["checked plaid", "striped", "plain solid-color", "floral"],
            "sleeve": ["long sleeves", "short sleeves", "long sleeves", "short sleeves"],
            "style": ["casual", "formal office", "casual", "vintage"],
        }
    )
    return Catalog(emb, table, tmp_path)
