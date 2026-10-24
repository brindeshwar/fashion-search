# API reference

The FastAPI backend (`src/fashion_search/api.py`) serves the Mirror web app, and you can call
it directly. Start it with `fashion-search serve`; the base URL is `http://127.0.0.1:8000`.

An interactive version of this reference, generated from the code, is at
**http://127.0.0.1:8000/docs** (Swagger UI) and `/openapi.json`.

The API has no authentication, so keep it on localhost. Errors are JSON:
`{"detail": "message"}`, or a list of field errors for 422 validation failures.

## Objects

**Item**: one garment in the catalogue.

```json
{
  "id": 42,
  "image_url": "/images/shirt.jpg",
  "tags": {
    "category": "button-up shirt",
    "color": "red",
    "pattern": "checked plaid",
    "sleeve": "long sleeves",
    "style": "casual"
  },
  "tryon_category": "tops",
  "score": 0.1312
}
```

`score` is the cosine similarity to the query (higher means closer), or `null` when there's
no query. `tryon_category` is `tops`, `bottoms` or `one-pieces`.

**TryOnJob**

```json
{
  "id": "3f9a1c0b7e2d",
  "status": "running",
  "queue_position": 0,
  "elapsed_seconds": 12.4,
  "expected_seconds": 55.0,
  "result_url": null,
  "error": null
}
```

`status` is `queued`, `running`, `done` or `error`. `expected_seconds` is the median of past
runs (55 s before the first one finishes). `result_url` is set once `status` is `done`.

## Endpoints

### `GET /api/health`

Server status, used for the app's status pill.

```json
{
  "version": "1.0.0",
  "items": 500,
  "tryon_available": true,
  "tryon_setup_hint": null,
  "gpu_warning": null,
  "garment_cleaning_available": true
}
```

`gpu_warning` explains when another process holds so much GPU memory that try-on will be
slow. `tryon_setup_hint` gives the install commands when try-on isn't available.
`garment_cleaning_available` is true when the BiRefNet weights for garment cleaning are downloaded.

### `GET /api/tags`

The tag values that actually occur in the catalogue, for each attribute.

```json
{ "color": ["beige", "black", "blue", "..."], "pattern": ["checked plaid", "..."], "...": [] }
```

### `GET /api/items`

Search and filter the catalogue.

| Query parameter | Type | Default | Meaning |
|---|---|---|---|
| `q` | string, ≤200 chars | (empty) | Text query. Results are ranked by similarity. Empty means catalogue order. |
| `limit` | int, 1–200 | 48 | Maximum number of items returned |
| `category`, `color`, `pattern`, `sleeve`, `style` | string | (none) | Exact tag match. Combine any of them with each other and with `q`. |

Response: `{"items": [Item, ...], "total": <number of items matching the filters>}`.

```bash
curl "http://127.0.0.1:8000/api/items?q=red%20plaid%20flannel&sleeve=long%20sleeves&limit=5"
```

### `POST /api/items/search-by-image`

Find the garments most similar to an uploaded photo. Send multipart form data with the field
`image`; the query parameter `limit` (1–200, default 48) is optional.

```bash
curl -F image=@my-shirt.jpg "http://127.0.0.1:8000/api/items/search-by-image?limit=10"
```

Response: `{"items": [...], "total": ...}`. Errors: 400 (not a readable image), 413 (over 15 MB).

### `GET /api/items/{id}`

A single item. Returns 404 if the id doesn't exist.

### `GET /images/{filename}`

The catalogue photo for an item (use `image_url` from an Item). Only files in the catalogue
are served; anything else is a 404. Responses are cached for a day.

### `POST /api/tryon`

Start a try-on. It returns immediately with **202 Accepted** and a TryOnJob; then poll it.

Multipart form fields:

| Field | Required | Meaning |
|---|---|---|
| `person` | yes | Photo of the person (file) |
| `garment_id` | one of these two | Catalogue item id |
| `garment` | one of these two | Garment photo (file), instead of `garment_id` |
| `category` | no | `tops`, `bottoms` or `one-pieces`. Taken from the item's tags by default, otherwise `tops`. |
| `garment_photo_type` | no | `model` (default; hanger or worn) or `flat-lay` |
| `steps` | no | 10–50, default 30 |
| `seed` | no | Integer, default 42 |
| `clean_garment` | no | `true` (default) removes the garment photo's background and crops to the garment before try-on; skipped if the BiRefNet weights are missing |

Errors: 503 (try-on not installed; `detail` has the setup commands), 422 (no garment, or an
invalid field), 400 and 413 (bad or oversized image).

```bash
curl -F person=@me.jpg -F garment_id=42 http://127.0.0.1:8000/api/tryon
```

### `GET /api/tryon/{job_id}`

The job's current state (TryOnJob). Poll about once a second. Returns 404 for unknown ids.
Jobs live in memory: the server keeps the last 50 and forgets them all on restart.

### `GET /api/tryon/{job_id}/result`

The finished image as `image/png`. Returns 404 until the job is `done`.

## Example: try-on from a script

```python
import time
import requests

base = "http://127.0.0.1:8000"
with open("me.jpg", "rb") as person:
    job = requests.post(
        f"{base}/api/tryon", files={"person": person}, data={"garment_id": 42}
    ).json()

while job["status"] in ("queued", "running"):
    time.sleep(1)
    job = requests.get(f"{base}/api/tryon/{job['id']}").json()

if job["status"] == "done":
    open("result.png", "wb").write(requests.get(base + job["result_url"]).content)
else:
    print("failed:", job["error"])
```

## Keeping the frontend in sync

`web/src/lib/api.ts` mirrors the pydantic models in `api.py`. Change both in the same commit
and add a test in `tests/test_api.py` (see [DEVELOPMENT.md](DEVELOPMENT.md#changing-the-api)).
