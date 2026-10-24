"""FastAPI backend for the React web app (``web/``).

Routes live under ``/api``; catalogue photos under ``/images``; the built frontend
(``web/dist``) is served at ``/`` when present, so one process serves everything.
Models load lazily on first use, so the API starts in about a second.
"""

import io
import time
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel

from . import __version__, tryon
from . import garment as garment_cleaning
from .catalog import Catalog
from .config import REPO_ROOT
from .jobs import JobQueue
from .taxonomy import ATTRIBUTES

MAX_UPLOAD_BYTES = 15 * 2**20
DEFAULT_TRYON_SECONDS = 55.0  # measured ~49 s at 30 steps on an RTX 4060, plus load
WEB_DIST = REPO_ROOT / "web" / "dist"


class Item(BaseModel):
    """One garment in the catalogue, as returned by the search endpoints."""

    id: int
    image_url: str
    tags: dict[str, str]
    tryon_category: tryon.FashnCategory
    score: float | None = None


class ItemList(BaseModel):
    """A page of search results plus how many items match the filters."""

    items: list[Item]
    total: int


class TryOnJob(BaseModel):
    """State of a background try-on job; poll until `status` is done or error."""

    id: str
    status: Literal["queued", "running", "done", "error"]
    queue_position: int
    elapsed_seconds: float
    expected_seconds: float
    result_url: str | None = None
    error: str | None = None


class Health(BaseModel):
    """Server status shown in the app's status pill."""

    version: str
    items: int
    tryon_available: bool
    tryon_setup_hint: str | None
    gpu_warning: str | None
    garment_cleaning_available: bool


def _read_image(upload: UploadFile) -> Image.Image:
    data = upload.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Image is larger than 15 MB.")
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError) as e:
        raise HTTPException(400, "That file isn't an image we can read.") from e
    # Phone photos store rotation in EXIF; apply it so people aren't sideways.
    return ImageOps.exif_transpose(img).convert("RGB")


def create_api(
    catalog: Catalog,
    embed_text: Callable[[str], np.ndarray] | None = None,
    embed_image: Callable[[Image.Image], np.ndarray] | None = None,
    jobs: JobQueue | None = None,
    web_dist: Path = WEB_DIST,
) -> FastAPI:
    """Build the app. The embed functions are injectable so tests don't load the model."""
    if embed_text is None or embed_image is None:
        from .core import embed_images, embed_texts

        embed_text = embed_text or (lambda q: embed_texts([q])[0])
        embed_image = embed_image or (lambda im: embed_images([im])[0])
    jobs = jobs or JobQueue()
    durations: list[float] = []
    files = set(catalog.table.file)

    app = FastAPI(title="Fashion Search API", version=__version__)

    def item(i: int, score: float | None = None) -> Item:
        """Build the API view of catalogue row `i`."""
        row = catalog.table.iloc[i]
        return Item(
            id=i,
            image_url=f"/images/{row.file}",
            tags={attr: str(row[attr]) for attr in ATTRIBUTES},
            tryon_category=tryon.fashn_category(str(row["category"])),
            score=None if score is None else round(score, 4),
        )

    def job_view(job) -> TryOnJob:
        """Build the API view of a job, with timing and queue position."""
        end = job.finished or time.time()
        expected = float(np.median(durations)) if durations else DEFAULT_TRYON_SECONDS
        return TryOnJob(
            id=job.id,
            status=job.status,
            queue_position=jobs.position(job),
            elapsed_seconds=round(end - job.started, 1) if job.started else 0.0,
            expected_seconds=round(expected, 1),
            result_url=f"/api/tryon/{job.id}/result" if job.status == "done" else None,
            error=job.error,
        )

    @app.get("/api/health", response_model=Health)
    def health():
        """Item count, try-on availability, and any GPU memory warning."""
        available = tryon.is_available()
        return Health(
            version=__version__,
            items=len(catalog),
            tryon_available=available,
            tryon_setup_hint=None if available else tryon.INSTALL_HINT,
            gpu_warning=tryon.low_vram_warning() if available else None,
            garment_cleaning_available=garment_cleaning.weights_ready(),
        )

    @app.get("/api/tags", response_model=dict[str, list[str]])
    def tags():
        """Tag values that occur in the catalogue, per attribute (for filter menus)."""
        return catalog.tag_values()

    @app.get("/api/items", response_model=ItemList)
    def list_items(
        q: Annotated[str, Query(max_length=200)] = "",
        limit: Annotated[int, Query(ge=1, le=200)] = 48,
        category: str | None = None,
        color: str | None = None,
        pattern: str | None = None,
        sleeve: str | None = None,
        style: str | None = None,
    ):
        """Search the catalogue: optional text query ranked by similarity, plus tag filters."""
        filters = dict(category=category, color=color, pattern=pattern, sleeve=sleeve, style=style)
        query = embed_text(q.strip()) if q.strip() else None
        total = len(catalog.filter(**filters))
        hits = catalog.search(query, limit, **filters)
        return ItemList(items=[item(i, s) for i, s in hits], total=total)

    @app.post("/api/items/search-by-image", response_model=ItemList)
    def search_by_image(image: UploadFile, limit: Annotated[int, Query(ge=1, le=200)] = 48):
        """Find the catalogue items most similar to an uploaded photo."""
        hits = catalog.top_k(embed_image(_read_image(image)), limit)
        return ItemList(items=[item(i, s) for i, s in hits], total=len(catalog))

    @app.get("/api/items/{item_id}", response_model=Item)
    def get_item(item_id: int):
        """A single catalogue item by id."""
        if not 0 <= item_id < len(catalog):
            raise HTTPException(404, "No such item.")
        return item(item_id)

    @app.get("/images/{filename}")
    def image(filename: str):
        """Serve a catalogue photo. Only files in the catalogue are served."""
        # Checking against the catalogue's own filenames also blocks path traversal.
        if filename not in files:
            raise HTTPException(404, "No such image.")
        cache = {"Cache-Control": "max-age=86400"}
        return FileResponse(catalog.image_dir / filename, headers=cache)

    @app.post("/api/tryon", response_model=TryOnJob, status_code=202)
    def start_tryon(
        person: Annotated[UploadFile, File(description="Photo of the person")],
        garment_id: Annotated[int | None, Form()] = None,
        garment: Annotated[UploadFile | None, File()] = None,
        category: Annotated[tryon.FashnCategory | None, Form()] = None,
        garment_photo_type: Annotated[tryon.GarmentPhotoType, Form()] = "model",
        steps: Annotated[int, Form(ge=10, le=50)] = 30,
        seed: Annotated[int, Form()] = 42,
        clean_garment: Annotated[bool, Form()] = True,
    ):
        """Start a try-on job (202). Poll `GET /api/tryon/{id}` for progress."""
        if not tryon.is_available():
            raise HTTPException(503, tryon.INSTALL_HINT)
        person_img = _read_image(person)
        if garment is not None:
            garment_img = _read_image(garment)
        elif garment_id is not None and 0 <= garment_id < len(catalog):
            garment_path = Path(catalog.path(garment_id))
            garment_img = None  # loaded on the worker: cleaning a new garment takes ~10 s
            tag = str(catalog.table.category.iloc[garment_id])
            category = category or tryon.fashn_category(tag)
        else:
            raise HTTPException(422, "Choose a garment from the catalogue or upload one.")

        def run() -> bytes:
            """Run the try-on on the job worker; returns PNG bytes."""
            t0 = time.time()
            image, clean = garment_img, clean_garment
            if image is None:  # a catalogue garment: use the on-disk cache of cleaned photos
                if clean and garment_cleaning.weights_ready():
                    image, clean = garment_cleaning.clean_file(garment_path), False
                else:
                    image = Image.open(garment_path).convert("RGB")
            out = tryon.try_on(
                person_img,
                image,
                category or "tops",
                garment_photo_type,
                steps,
                seed,
                clean=clean,
            )
            durations.append(time.time() - t0)
            buf = io.BytesIO()
            out.save(buf, format="PNG")
            return buf.getvalue()

        return job_view(jobs.submit(run))

    @app.get("/api/tryon/{job_id}", response_model=TryOnJob)
    def tryon_status(job_id: str):
        """Current state of a try-on job."""
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(404, "No such try-on job.")
        return job_view(job)

    @app.get("/api/tryon/{job_id}/result")
    def tryon_result(job_id: str):
        """The finished try-on image as PNG (404 until the job is done)."""
        job = jobs.get(job_id)
        if job is None or job.status != "done":
            raise HTTPException(404, "Result isn't ready.")
        return Response(job.result, media_type="image/png")

    if (web_dist / "index.html").exists():
        app.mount("/", StaticFiles(directory=web_dist, html=True), name="web")
    return app


def serve(catalog: Catalog, host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the API and the built web app with uvicorn."""
    import uvicorn

    uvicorn.run(create_api(catalog), host=host, port=port)
