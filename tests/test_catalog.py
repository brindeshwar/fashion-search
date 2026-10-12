import numpy as np
import pytest

from fashion_search.catalog import Catalog


def test_top_k_returns_most_similar_first(catalog):
    query = np.zeros(8, np.float32)
    query[2], query[0] = 0.9, 0.4
    assert [i for i, _ in catalog.top_k(query, 2)] == [2, 0]


def test_top_k_scores_are_cosine(catalog):
    query = catalog.embeddings[1]
    (i, score), *_ = catalog.top_k(query, 1)
    assert i == 1 and score == pytest.approx(1.0)


def test_filter_combines_tags(catalog):
    assert list(catalog.filter(color="red", sleeve="long sleeves")) == [0, 2]
    assert list(catalog.filter(color="red", pattern="striped")) == []


def test_filter_ignores_any_and_none(catalog):
    assert len(catalog.filter(color="any", pattern=None)) == len(catalog)


def test_filter_rejects_unknown_attribute(catalog):
    with pytest.raises(KeyError):
        catalog.filter(fabric="linen")


def test_save_load_roundtrip(catalog, tmp_path):
    catalog.save(tmp_path / "idx")
    loaded = Catalog.load(tmp_path / "idx", catalog.image_dir)
    np.testing.assert_array_equal(loaded.embeddings, catalog.embeddings)
    assert loaded.table.equals(catalog.table)
    assert loaded.path(0).endswith("a.jpg")


def test_load_missing_index_has_helpful_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="fashion-search index"):
        Catalog.load(tmp_path, tmp_path)
