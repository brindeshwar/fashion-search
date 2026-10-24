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


def test_add_remove_and_index_of(catalog):
    emb = np.zeros(8, np.float32)
    emb[5] = 1
    tags = {
        "category": "blouse",
        "color": "red",
        "pattern": "floral",
        "sleeve": "long sleeves",
        "style": "casual",
    }
    i = catalog.add("upload-x.jpg", emb, tags)
    assert i == 4 and len(catalog) == 5 and catalog.embeddings.shape == (5, 8)
    assert catalog.is_upload(4) and not catalog.is_upload(0)
    assert catalog.index_of("upload-x.jpg") == 4 and catalog.index_of("nope.jpg") is None
    assert catalog.top_k(emb, 1)[0][0] == 4
    assert catalog.remove(1) == "b.jpg"
    assert catalog.index_of("upload-x.jpg") == 3 and catalog.embeddings.shape == (4, 8)
    assert catalog.top_k(emb, 1)[0][0] == 3  # embeddings stay aligned with rows
