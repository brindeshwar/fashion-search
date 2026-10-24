from fashion_search.store import Look, LookStore


def look(i, duration=50.0, created=None):
    return Look(
        id=f"job{i}",
        created=created if created is not None else float(i),
        garment_id=i,
        garment_label="red checked plaid",
        garment_photo_type="model",
        steps=30,
        seed=42,
        clean_garment=True,
        duration_seconds=duration,
    )


def test_add_get_list_newest_first(tmp_path):
    store = LookStore(tmp_path / "m.db", tmp_path / "looks")
    for i in range(3):
        store.add(look(i), b"png")
    assert [lk.id for lk in store.list()] == ["job2", "job1", "job0"]
    assert store.get("job1") == look(1)
    assert store.get("missing") is None
    assert store.image_path("job1").read_bytes() == b"png"


def test_list_limit_and_median(tmp_path):
    store = LookStore(tmp_path / "m.db", tmp_path / "looks")
    assert store.median_duration() is None
    for i, d in enumerate([40.0, 60.0, 50.0]):
        store.add(look(i, duration=d), b"png")
    assert len(store.list(limit=2)) == 2
    assert store.median_duration() == 50.0


def test_reopening_keeps_data(tmp_path):
    LookStore(tmp_path / "m.db", tmp_path / "looks").add(look(7), b"png")
    assert LookStore(tmp_path / "m.db", tmp_path / "looks").get("job7") == look(7)
