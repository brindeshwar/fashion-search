import io
import time

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from fashion_search import garment as garment_cleaning
from fashion_search import tryon
from fashion_search.api import create_api
from fashion_search.jobs import JobQueue


def png_bytes(color="red") -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (16, 16), color).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def client(catalog, tmp_path, monkeypatch):
    # Never run the real garment-cleaning model in fast tests, even if its weights exist.
    monkeypatch.setattr(garment_cleaning, "weights_ready", lambda *a: False)
    for f in catalog.table.file:
        Image.new("RGB", (8, 8)).save(catalog.image_dir / f)
    # Fake embeddings: the query "points at" item 2; any uploaded image points at item 1.
    api = create_api(
        catalog,
        embed_text=lambda q: catalog.embeddings[2],
        embed_image=lambda im: catalog.embeddings[1],
        jobs=JobQueue(),
        web_dist=tmp_path / "no-dist",
    )
    return TestClient(api)


def test_health(client, monkeypatch):
    monkeypatch.setattr(tryon, "is_available", lambda *a: False)
    body = client.get("/api/health").json()
    assert body["items"] == 4 and body["tryon_available"] is False
    assert "tryon-download" in body["tryon_setup_hint"]


def test_tags_only_lists_values_in_catalogue(client):
    tags = client.get("/api/tags").json()
    assert tags["color"] == ["blue", "red", "white"]


def test_items_without_query_returns_catalogue(client):
    body = client.get("/api/items").json()
    assert body["total"] == 4 and [i["id"] for i in body["items"]] == [0, 1, 2, 3]
    assert body["items"][0]["image_url"] == "/images/a.jpg"
    assert body["items"][3]["tryon_category"] == "tops"


def test_items_combines_text_query_and_filters(client):
    body = client.get("/api/items", params={"q": "red shirt", "color": "red"}).json()
    assert body["total"] == 2
    assert [i["id"] for i in body["items"]] == [2, 0]  # filtered to red, ranked by query
    assert body["items"][0]["score"] == pytest.approx(1.0)


def test_search_by_image(client):
    body = client.post(
        "/api/items/search-by-image", files={"image": ("x.png", png_bytes(), "image/png")}
    ).json()
    assert body["items"][0]["id"] == 1


def test_search_by_image_rejects_non_images(client):
    files = {"image": ("x.txt", b"hello", "text/plain")}
    r = client.post("/api/items/search-by-image", files=files)
    assert r.status_code == 400


def test_images_only_serves_catalogue_files(client):
    assert client.get("/images/a.jpg").status_code == 200
    assert client.get("/images/..%2F..%2Fpyproject.toml").status_code == 404
    assert client.get("/images/nope.jpg").status_code == 404


def test_tryon_unavailable_returns_503(client, monkeypatch):
    monkeypatch.setattr(tryon, "is_available", lambda *a: False)
    r = client.post("/api/tryon", files={"person": ("p.png", png_bytes(), "image/png")})
    assert r.status_code == 503


def test_tryon_requires_a_garment(client, monkeypatch):
    monkeypatch.setattr(tryon, "is_available", lambda *a: True)
    r = client.post("/api/tryon", files={"person": ("p.png", png_bytes(), "image/png")})
    assert r.status_code == 422


def test_tryon_job_lifecycle(client, monkeypatch):
    calls = {}

    def fake_try_on(person, garment, category, photo_type, steps, seed, clean):
        calls.update(category=category, photo_type=photo_type, steps=steps, clean=clean)
        return Image.new("RGB", (4, 4), "green")

    monkeypatch.setattr(tryon, "is_available", lambda *a: True)
    monkeypatch.setattr(tryon, "try_on", fake_try_on)
    r = client.post(
        "/api/tryon",
        files={"person": ("p.png", png_bytes(), "image/png")},
        data={"garment_id": "3", "steps": "20", "clean_garment": "false"},
    )
    assert r.status_code == 202
    job_id = r.json()["id"]

    for _ in range(100):
        job = client.get(f"/api/tryon/{job_id}").json()
        if job["status"] in ("done", "error"):
            break
        time.sleep(0.02)
    assert job["status"] == "done", job
    assert calls == {"category": "tops", "photo_type": "model", "steps": 20, "clean": False}
    result = client.get(job["result_url"])
    assert result.headers["content-type"] == "image/png"
    assert Image.open(io.BytesIO(result.content)).size == (4, 4)


def test_tryon_errors_are_reported(client, monkeypatch):
    def boom(*a, **kw):
        raise RuntimeError("CUDA out of memory")

    monkeypatch.setattr(tryon, "is_available", lambda *a: True)
    monkeypatch.setattr(tryon, "try_on", boom)
    job_id = client.post(
        "/api/tryon",
        files={"person": ("p.png", png_bytes(), "image/png")},
        data={"garment_id": "0"},
    ).json()["id"]
    for _ in range(100):
        job = client.get(f"/api/tryon/{job_id}").json()
        if job["status"] == "error":
            break
        time.sleep(0.02)
    assert job["error"] == "CUDA out of memory"
    assert client.get(f"/api/tryon/{job_id}/result").status_code == 404


def test_catalog_search_without_query_keeps_order(catalog):
    assert catalog.search(None, 10, sleeve="short sleeves") == [(1, None), (3, None)]


def test_catalog_search_ranks_within_filter(catalog):
    q = np.zeros(8, np.float32)
    q[0] = 1
    assert catalog.search(q, 1, color="red")[0][0] == 0
