# Data

Everything in `data/` except this file is git-ignored (see ADR-004 in `docs/DECISIONS.md`).

| Folder | Contents | How to get it |
|---|---|---|
| `shirts/` | The garment catalogue: any JPG, PNG or WEBP photos. The original 500 photos came from second-hand marketplace listings in 2025 and can't be redistributed. | Add your own photos |
| `fashion_mnist/` | Fashion-MNIST, used only by `fashion-search evaluate` | Downloaded automatically on first run |

Photos of a single garment on a hanger, a person or a plain background work best, both for
tagging and for try-on.

Garments added from the web app ("Add yours") are saved here too, as `upload-<id>.jpg`. The
prefix marks them as yours: only they can be deleted from the app, and they stay yours after a
re-index.

To use a different folder without moving files:

```bash
fashion-search index --data-dir path/to/photos
fashion-search serve --data-dir path/to/photos
```

Or set `FASHION_DATA_DIR`. Rerun `fashion-search index` after adding or removing photos;
the index goes to `artifacts/index/` (`FASHION_INDEX_DIR`).
