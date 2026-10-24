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
from fashion_search.store import LookStore


def png_bytes(color="red") -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (16, 16), color).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def store(tmp_path):
    return LookStore(tmp_path / "mirror.db", tmp_path / "looks")


def fake_tags(emb):
    return [
        {
            "category": "t-shirt",
            "color": "green",
            "pattern": "striped",
            "sleeve": "short sleeves",
            "style": "casual",
        }
        for _ in emb
    ]


def make_api(catalog, tmp_path, store):
    # Fake embeddings: the query "points at" item 2; any uploaded image points at item 1.
    return create_api(
        catalog,
        embed_text=lambda q: catalog.embeddings[2],
        embed_image=lambda im: catalog.embeddings[1],
        jobs=JobQueue(),
        web_dist=tmp_path / "no-dist",
        store=store,
        index_dir=tmp_path / "index",
        tag_rows=fake_tags,
    )


@pytest.fixture
def client(catalog, tmp_path, monkeypatch, store):
    # Never run the real garment-cleaning model in fast tests, even if its weights exist.
    monkeypatch.setattr(garment_cleaning, "weights_ready", lambda *a: False)
    for f in catalog.table.file:
        Image.new("RGB", (8, 8)).save(catalog.image_dir / f)
    return TestClient(make_api(catalog, tmp_path, store))


def run_tryon(client, monkeypatch, **data):
    """Start a try-on with a fake model and wait for it to finish."""
    monkeypatch.setattr(tryon, "is_available", lambda *a: True)
    monkeypatch.setattr(tryon, "try_on", lambda *a, **kw: Image.new("RGB", (4, 4), "green"))
    files = {"person": ("p.png", png_bytes(), "image/png")}
    job = client.post("/api/tryon", files=files, data=data).json()
    for _ in range(200):
        job = client.get(f"/api/tryon/{job['id']}").json()
        if job["status"] in ("done", "error"):
            return job
        time.sleep(0.02)
    raise AssertionError(f"try-on did not finish: {job}")


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


def test_finished_tryon_is_saved_as_a_look(client, monkeypatch):
    job = run_tryon(client, monkeypatch, garment_id="0", steps="20")
    assert job["result_url"] == f"/api/looks/{job['id']}/image"
    looks = client.get("/api/looks").json()["looks"]
    assert [lk["id"] for lk in looks] == [job["id"]]
    look = looks[0]
    assert look["garment_label"] == "red checked plaid"
    assert look["garment_image_url"] == "/images/a.jpg"
    assert (look["steps"], look["garment_photo_type"]) == (20, "model")
    image = client.get(look["image_url"])
    assert image.headers["content-type"] == "image/png"


def test_looks_survive_a_restart(catalog, tmp_path, monkeypatch, store, client):
    job = run_tryon(client, monkeypatch, garment_id="1")
    restarted = TestClient(make_api(catalog, tmp_path, store))  # fresh jobs, same store
    assert [lk["id"] for lk in restarted.get("/api/looks").json()["looks"]] == [job["id"]]
    status = restarted.get(f"/api/tryon/{job['id']}").json()
    assert status["status"] == "done" and status["result_url"].endswith("/image")
    assert restarted.get(f"/api/tryon/{job['id']}/result").status_code == 200
    health_eta = restarted.post(
        "/api/tryon",
        files={"person": ("p.png", png_bytes(), "image/png")},
        data={"garment_id": "0"},
    ).json()["expected_seconds"]
    assert health_eta == store.median_duration()  # estimate comes from saved looks


def test_delete_look_removes_row_and_image(client, monkeypatch, store):
    job = run_tryon(client, monkeypatch, garment_id="0")
    assert store.image_path(job["id"]).exists()
    assert client.delete(f"/api/looks/{job['id']}").status_code == 204
    assert client.get("/api/looks").json()["looks"] == []
    assert not store.image_path(job["id"]).exists()
    assert client.delete(f"/api/looks/{job['id']}").status_code == 404
    assert client.get(f"/api/looks/{job['id']}/image").status_code == 404


def test_look_image_rejects_unknown_ids(client):
    assert client.get("/api/looks/..%2F..%2Fpyproject.toml/image").status_code == 404
    assert client.get("/api/looks/nope/image").status_code == 404


def test_uploaded_garment_look_has_no_catalogue_link(client, monkeypatch):
    monkeypatch.setattr(tryon, "is_available", lambda *a: True)
    monkeypatch.setattr(tryon, "try_on", lambda *a, **kw: Image.new("RGB", (4, 4)))
    files = {
        "person": ("p.png", png_bytes(), "image/png"),
        "garment": ("g.png", png_bytes("blue"), "image/png"),
    }
    job_id = client.post("/api/tryon", files=files).json()["id"]
    for _ in range(200):
        if client.get(f"/api/tryon/{job_id}").json()["status"] == "done":
            break
        time.sleep(0.02)
    look = client.get("/api/looks").json()["looks"][0]
    assert (look["garment_id"], look["garment_image_url"]) == (None, None)
    assert look["garment_label"] == "Uploaded garment"


def upload(client, color="blue"):
    files = {"image": ("mine.png", png_bytes(color), "image/png")}
    return client.post("/api/items", files=files)


def test_upload_adds_a_searchable_tagged_item(client, catalog, tmp_path):
    r = upload(client)
    assert r.status_code == 201
    new = r.json()
    assert new["id"] == 4 and new["uploaded"] is True
    assert new["tags"]["color"] == "green" and new["image_url"].startswith("/images/upload-")
    assert client.get(new["image_url"]).status_code == 200
    assert client.get("/api/items").json()["total"] == 5
    assert client.get("/api/items", params={"color": "green"}).json()["total"] == 1
    assert (tmp_path / "index" / "catalog.csv").exists()  # saved, so it survives a restart
    assert client.get("/api/items/0").json()["uploaded"] is False
    mine = client.get("/api/items", params={"uploaded": "true"}).json()
    assert mine["total"] == 1 and mine["items"][0]["id"] == new["id"]


def test_upload_rejects_non_images(client):
    files = {"image": ("x.txt", b"nope", "text/plain")}
    assert client.post("/api/items", files=files).status_code == 400


def test_only_uploads_can_be_deleted(client, catalog):
    assert client.delete("/api/items/0").status_code == 403
    assert client.delete("/api/items/99").status_code == 404
    new = upload(client).json()
    path = catalog.image_dir / new["image_url"].removeprefix("/images/")
    assert client.delete(f"/api/items/{new['id']}").status_code == 204
    assert not path.exists()
    assert client.get("/api/items").json()["total"] == 4
    assert client.get(new["image_url"]).status_code == 404


def test_looks_follow_their_garment_when_rows_shift(client, monkeypatch):
    first, second = upload(client).json(), upload(client, "red").json()
    look_job = run_tryon(client, monkeypatch, garment_id=str(second["id"]))
    assert client.delete(f"/api/items/{first['id']}").status_code == 204
    look = client.get("/api/looks").json()["looks"][0]
    assert look["id"] == look_job["id"]
    assert look["garment_id"] == second["id"] - 1  # moved up one row, still the same garment
    assert look["garment_image_url"] == second["image_url"]
    assert client.delete(f"/api/items/{look['garment_id']}").status_code == 204
    gone = client.get("/api/looks").json()["looks"][0]
    assert (gone["garment_id"], gone["garment_image_url"]) == (None, None)
