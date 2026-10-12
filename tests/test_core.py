import numpy as np
import pytest

from fashion_search.core import softmax_scores
from fashion_search.taxonomy import ATTRIBUTES


def test_softmax_rows_sum_to_one_and_pick_best_match():
    images = np.eye(3, dtype=np.float32)
    texts = np.eye(3, dtype=np.float32)[[2, 0, 1]]
    probs = softmax_scores(images, texts, scale=100.0)
    np.testing.assert_allclose(probs.sum(axis=1), 1.0, rtol=1e-6)
    assert list(probs.argmax(axis=1)) == [1, 2, 0]


def test_softmax_is_stable_for_large_scale():
    probs = softmax_scores(np.ones((1, 2)), np.eye(2), scale=1e6)
    assert np.isfinite(probs).all()


@pytest.mark.parametrize("attr", list(ATTRIBUTES))
def test_taxonomy_is_well_formed(attr):
    template, labels = ATTRIBUTES[attr]
    assert template.count("{}") == 1
    assert len(labels) >= 2
    assert len(labels) == len(set(labels)), "duplicate labels"


@pytest.mark.slow
def test_real_model_tags_a_shirt_as_a_shirt():
    """Downloads FashionSigLIP (~800 MB). Run with: pytest -m slow"""
    from PIL import Image

    from fashion_search.core import embed_images, zero_shot

    img = Image.new("RGB", (224, 224), "white")
    emb = embed_images([img])
    assert emb.shape == (1, 768)
    np.testing.assert_allclose(np.linalg.norm(emb, axis=1), 1.0, rtol=1e-3)
    probs = zero_shot(emb, ["shirt", "shoe"], "a photo of a {}")
    np.testing.assert_allclose(probs.sum(), 1.0, rtol=1e-5)
