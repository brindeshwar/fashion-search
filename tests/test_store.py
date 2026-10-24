from fashion_search.store import Look, LookStore


def look(i, duration=50.0, created=None):
    return Look(
        id=f"job{i}",
        created=created if created is not None else float(i),
        garment_file=f"shirt{i}.jpg",
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


def test_old_database_without_garment_file_is_migrated(tmp_path):
    import sqlite3

    db = tmp_path / "m.db"
    with sqlite3.connect(db) as conn:  # the schema saved looks shipped with first
        conn.execute(
            "CREATE TABLE looks (id TEXT PRIMARY KEY, created REAL NOT NULL, garment_id INTEGER,"
            " garment_label TEXT NOT NULL, garment_photo_type TEXT NOT NULL,"
            " steps INTEGER NOT NULL,"
            " seed INTEGER NOT NULL, clean_garment INTEGER NOT NULL,"
            " duration_seconds REAL NOT NULL)"
        )
        conn.execute("INSERT INTO looks VALUES ('old', 1, 3, 'red', 'model', 30, 42, 1, 50)")
    store = LookStore(db, tmp_path / "looks")
    assert store.get("old").garment_file is None and store.get("old").garment_label == "red"
    store.add(look(1, created=5.0), b"png")
    assert [lk.id for lk in store.list()] == ["job1", "old"]
