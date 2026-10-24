import numpy as np
import pytest
from PIL import Image

from fashion_search import garment


def photo(w=100, h=80, color=(200, 30, 30)):
    return Image.new("RGB", (w, h), color)


def square_mask(w=100, h=80, box=(20, 10, 60, 50)):
    m = np.zeros((h, w), np.float32)
    left, top, right, bottom = box
    m[top:bottom, left:right] = 1.0
    return m


def test_crops_to_mask_with_margin():
    out = garment.composite_and_crop(photo(), square_mask(), margin=0.1)
    # 40x40 box, 10% margin = 3 px each side (int of 0.1 * 39)
    assert out.size == (46, 46)


def test_background_becomes_white_and_garment_is_kept():
    out = np.asarray(garment.composite_and_crop(photo(), square_mask(), margin=0.1))
    assert tuple(out[0, 0]) == (255, 255, 255)  # margin area is outside the mask
    assert tuple(out[20, 20]) == (200, 30, 30)  # inside the garment


def test_empty_mask_returns_the_original_photo():
    img = photo()
    out = garment.composite_and_crop(img, np.zeros((80, 100), np.float32))
    assert out.size == img.size
    assert np.array_equal(np.asarray(out), np.asarray(img))


def test_crop_is_clamped_to_the_image():
    out = garment.composite_and_crop(photo(), square_mask(box=(0, 0, 100, 80)), margin=0.5)
    assert out.size == (100, 80)


def test_weights_ready_checks_size(tmp_path):
    path = tmp_path / "model.onnx"
    assert not garment.weights_ready(path)
    path.write_bytes(b"partial")
    assert not garment.weights_ready(path)


def test_clean_file_caches_by_file(tmp_path, monkeypatch):
    calls = []

    def fake_clean(img):
        calls.append(1)
        return img.convert("RGB")

    monkeypatch.setattr(garment, "clean_garment", fake_clean)
    src = tmp_path / "shirt.jpg"
    photo().save(src)
    first = garment.clean_file(src, cache_dir=tmp_path / "cache")
    second = garment.clean_file(src, cache_dir=tmp_path / "cache")
    assert len(calls) == 1 and first.size == second.size == (100, 80)


@pytest.mark.slow
def test_real_birefnet_finds_a_garment_on_a_plain_background():
    """Needs the BiRefNet weights (`fashion-search tryon-download`). Run with: pytest -m slow"""
    if not garment.weights_ready():
        pytest.skip("BiRefNet weights not downloaded")
    img = Image.new("RGB", (400, 500), "white")
    img.paste(Image.new("RGB", (200, 260), (30, 60, 160)), (100, 120))
    mask = garment.predict_mask(img)
    assert mask.shape == (500, 400)
    assert mask[250, 200] > 0.5 and mask[20, 20] < 0.5
