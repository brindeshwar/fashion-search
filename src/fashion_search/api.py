"""FastAPI backend for the React web app (``web/``).

Routes live under ``/api``; catalogue photos under ``/images``; the built frontend
(``web/dist``) is served at ``/`` when present, so one process serves everything.
Models load lazily on first use, so the API starts in about a second.
"""

import io
import threading
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel

from . import __version__, tryon
from . import garment as garment_cleaning
from .catalog import UPLOAD_PREFIX, Catalog
from .config import DB_PATH, INDEX_DIR, LOOKS_DIR, REPO_ROOT
from .jobs import Job, JobQueue
from .store import Look, LookStore
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
    uploaded: bool = False


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


class SavedLook(BaseModel):
    """A finished try-on, kept across restarts until deleted."""

    id: str
    created: float
    image_url: str
    garment_id: int | None
    garment_label: str
    garment_image_url: str | None
    garment_photo_type: str
    steps: int
    seed: int
    clean_garment: bool
    duration_seconds: float


class LookList(BaseModel):
    """Saved looks, most recent first."""

    looks: list[SavedLook]


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
    store: LookStore | None = None,
    index_dir: Path = INDEX_DIR,
    tag_rows: Callable[[np.ndarray], list[dict]] | None = None,
) -> FastAPI:
    """Build the app. Models, storage and paths are injectable so tests don't touch them."""
    if embed_text is None or embed_image is None:
        from .core import embed_images, embed_texts

        embed_text = embed_text or (lambda q: embed_texts([q])[0])
        embed_image = embed_image or (lambda im: embed_images([im])[0])
    if tag_rows is None:
        from .indexing import tag_rows
    jobs = jobs or JobQueue()
    store = store or LookStore(DB_PATH, LOOKS_DIR)
    durations: list[float] = []
    files = set(catalog.table.file)
    edit_lock = threading.Lock()  # one catalogue change (and index save) at a time

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
            uploaded=catalog.is_upload(i),
        )

    def job_view(job) -> TryOnJob:
        """Build the API view of a job, with timing and queue position."""
        end = job.finished or time.time()
        if durations:
            expected = float(np.median(durations))
        else:  # after a restart, estimate from saved looks
            saved = store.median_duration()
            expected = saved if saved is not None else DEFAULT_TRYON_SECONDS
        return TryOnJob(
            id=job.id,
            status=job.status,
            queue_position=jobs.position(job),
            elapsed_seconds=round(end - job.started, 1) if job.started else 0.0,
            expected_seconds=round(expected, 1),
            result_url=f"/api/looks/{job.id}/image" if job.status == "done" else None,
            error=job.error,
        )

    def saved_look(look: Look) -> SavedLook:
        """Build the API view of a saved look (the garment may since have been deleted)."""
        fields = vars(look).copy()
        file = fields.pop("garment_file")
        row = catalog.index_of(file) if file else None
        return SavedLook(
            **fields,
            garment_id=row,
            image_url=f"/api/looks/{look.id}/image",
            garment_image_url=item(row).image_url if row is not None else None,
        )

    def garment_label(row: int | None) -> str:
        """Short description of the garment for the looks list."""
        if row is None:
            return "Uploaded garment"
        tags = catalog.table.iloc[row]
        return f"{tags['color']} {tags['pattern']}"

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
        uploaded: bool = False,
    ):
        """Search the catalogue: optional text query ranked by similarity, plus tag filters.

        `uploaded=true` limits results to garments you added.
        """
        filters = dict(category=category, color=color, pattern=pattern, sleeve=sleeve, style=style)
        query = embed_text(q.strip()) if q.strip() else None
        total = len(catalog.filter(uploaded, **filters))
        hits = catalog.search(query, limit, uploaded, **filters)
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

    @app.post("/api/items", response_model=Item, status_code=201)
    def add_item(image: UploadFile):
        """Add your own garment photo: it's saved, tagged and searchable straight away."""
        img = _read_image(image)
        img.thumbnail((2048, 2048))  # plenty for search and try-on; keeps the folder small
        emb = embed_image(img)
        tags = tag_rows(emb[None])[0]
        file = f"{UPLOAD_PREFIX}{uuid.uuid4().hex[:12]}.jpg"
        with edit_lock:
            img.save(catalog.image_dir / file, quality=92)
            i = catalog.add(file, emb, tags)
            catalog.save(index_dir)
            files.add(file)
        return item(i)

    @app.delete("/api/items/{item_id}", status_code=204)
    def delete_item(item_id: int):
        """Delete a garment you added. The original catalogue can't be deleted here."""
        with edit_lock:
            if not 0 <= item_id < len(catalog):
                raise HTTPException(404, "No such item.")
            if not catalog.is_upload(item_id):
                raise HTTPException(403, "Only garments you added can be deleted.")
            file = catalog.remove(item_id)
            catalog.save(index_dir)
            files.discard(file)
        (catalog.image_dir / file).unlink(missing_ok=True)

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
        garment_file: str | None = None
        if garment is not None:
            garment_img = _read_image(garment)
        elif garment_id is not None and 0 <= garment_id < len(catalog):
            garment_path = Path(catalog.path(garment_id))
            garment_file = garment_path.name
            garment_img = None  # loaded on the worker: cleaning a new garment takes ~10 s
            tag = str(catalog.table.category.iloc[garment_id])
            category = category or tryon.fashn_category(tag)
        else:
            raise HTTPException(422, "Choose a garment from the catalogue or upload one.")

        label = garment_label(garment_id if garment is None else None)  # before rows can shift

        def run(job: Job) -> bytes:
            """Run the try-on on the job worker, save it as a look, return PNG bytes."""
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
            duration = time.time() - t0
            durations.append(duration)
            buf = io.BytesIO()
            out.save(buf, format="PNG")
            look = Look(
                id=job.id,
                created=time.time(),
                garment_file=garment_file,
                garment_label=label,
                garment_photo_type=garment_photo_type,
                steps=steps,
                seed=seed,
                clean_garment=clean_garment,
                duration_seconds=round(duration, 1),
            )
            store.add(look, buf.getvalue())
            return buf.getvalue()

        return job_view(jobs.submit(run))

    @app.get("/api/tryon/{job_id}", response_model=TryOnJob)
    def tryon_status(job_id: str):
        """Current state of a try-on job (also answers for looks saved before a restart)."""
        job = jobs.get(job_id)
        if job is not None:
            return job_view(job)
        look = store.get(job_id)
        if look is None:
            raise HTTPException(404, "No such try-on job.")
        return TryOnJob(
            id=look.id,
            status="done",
            queue_position=0,
            elapsed_seconds=look.duration_seconds,
            expected_seconds=look.duration_seconds,
            result_url=f"/api/looks/{look.id}/image",
        )

    @app.get("/api/tryon/{job_id}/result")
    def tryon_result(job_id: str):
        """The finished try-on image as PNG (404 until the job is done)."""
        return look_image(job_id)

    @app.get("/api/looks", response_model=LookList)
    def list_looks(limit: Annotated[int, Query(ge=1, le=200)] = 50):
        """Saved try-on results, most recent first."""
        return LookList(looks=[saved_look(lk) for lk in store.list(limit)])

    @app.get("/api/looks/{look_id}/image")
    def look_image(look_id: str):
        """A saved look's image as PNG."""
        path = store.image_path(look_id)
        # Only ids that exist in the database are served, which also blocks path tricks.
        if store.get(look_id) is None or not path.exists():
            raise HTTPException(404, "Result isn't ready.")
        return FileResponse(path, media_type="image/png")

    @app.delete("/api/looks/{look_id}", status_code=204)
    def delete_look(look_id: str):
        """Delete a saved look and its image."""
        if not store.delete(look_id):
            raise HTTPException(404, "No such look.")

    if (web_dist / "index.html").exists():
        app.mount("/", StaticFiles(directory=web_dist, html=True), name="web")
    return app


def serve(catalog: Catalog, host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the API and the built web app with uvicorn."""
    import uvicorn

    uvicorn.run(create_api(catalog), host=host, port=port)
