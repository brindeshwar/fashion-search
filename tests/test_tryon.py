from types import SimpleNamespace

import pytest
from PIL import Image

from fashion_search import tryon
from fashion_search.cli import build_parser


@pytest.mark.parametrize(
    ("tag", "expected"),
    [("dress", "one-pieces"), ("button-up shirt", "tops"), ("jacket", "tops")],
)
def test_fashn_category_mapping(tag, expected):
    assert tryon.fashn_category(tag) == expected


def test_weights_ready_needs_every_file(tmp_path):
    assert not tryon.weights_ready(tmp_path)
    (tmp_path / "dwpose").mkdir()
    for name in ["model.safetensors", *(f"dwpose/{f}" for f in tryon.DWPOSE_FILES)]:
        assert not tryon.weights_ready(tmp_path)
        (tmp_path / name).touch()
    assert tryon.weights_ready(tmp_path)


def test_try_on_passes_options_to_pipeline(monkeypatch):
    calls = {}
    out = Image.new("RGB", (8, 8), "blue")

    def fake_pipeline(**kwargs):
        calls.update(kwargs)
        return SimpleNamespace(images=[out])

    monkeypatch.setattr(tryon, "load_pipeline", lambda: fake_pipeline)
    person = Image.new("L", (8, 8))
    result = tryon.try_on(person, Image.new("RGBA", (8, 8)), "one-pieces", "model", 20, 7)

    assert result is out
    assert calls["person_image"].mode == "RGB" and calls["garment_image"].mode == "RGB"
    assert (calls["category"], calls["garment_photo_type"]) == ("one-pieces", "model")
    assert (calls["num_timesteps"], calls["seed"]) == (20, 7)


def test_load_pipeline_without_setup_explains_how_to_install(monkeypatch, tmp_path):
    tryon.load_pipeline.cache_clear()
    with pytest.raises(RuntimeError, match="tryon-download"):
        tryon.load_pipeline(tmp_path)


def test_app_shows_setup_hint_when_tryon_unavailable(monkeypatch, catalog):
    from fashion_search.app import build_app

    monkeypatch.setattr(tryon, "is_available", lambda *a: False)
    assert build_app(catalog) is not None


def test_app_builds_tryon_tab_when_available(monkeypatch, catalog):
    from fashion_search.app import build_app

    monkeypatch.setattr(tryon, "is_available", lambda *a: True)
    assert build_app(catalog) is not None


def test_tryon_cli_args():
    args = build_parser().parse_args(
        ["tryon", "--person", "p.jpg", "--garment", "g.jpg", "--category", "one-pieces"]
    )
    assert args.category == "one-pieces" and args.steps == 30 and args.out.name == "tryon.png"


@pytest.mark.slow
def test_real_tryon_returns_an_image():
    """Needs the [tryon] extra + weights. Run with: pytest -m slow"""
    if not tryon.is_available():
        pytest.skip(tryon.INSTALL_HINT)
    person = Image.new("RGB", (384, 512), "grey")
    garment = Image.new("RGB", (384, 512), "red")
    result = tryon.try_on(person, garment, steps=10)
    assert isinstance(result, Image.Image)
