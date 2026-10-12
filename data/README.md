# Data

Everything in `data/` except this file is git-ignored (see `docs/DECISIONS.md`, ADR-004).

| Folder | Contents | How to get it |
|---|---|---|
| `shirts/` | 500 shirt photos (JPG, ~106 MB) collected in 2025 from second-hand marketplace listings for the original project | Not redistributable. Use your own photos: any folder of JPG/PNG/WEBP images works |
| `fashion_mnist/` | Fashion-MNIST, only used by `fashion-search evaluate` | Downloaded automatically by torchvision on first run |

To use a different folder without moving files:

```bash
fashion-search index --data-dir path/to/photos
fashion-search app   --data-dir path/to/photos
```

Or set `FASHION_DATA_DIR`. Generated indexes go to `artifacts/index/` (`FASHION_INDEX_DIR`).
