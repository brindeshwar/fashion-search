"""Saved looks: try-on results that survive a server restart.

Metadata lives in SQLite (`mirror.db`); each result image is a PNG file next to it, so the
database stays small and images can be served straight from disk. The person's own
photo is never stored, only the finished result.
"""

import sqlite3
import statistics
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS looks (
    id                 TEXT PRIMARY KEY,
    created            REAL NOT NULL,
    garment_id         INTEGER,
    garment_label      TEXT NOT NULL,
    garment_photo_type TEXT NOT NULL,
    steps              INTEGER NOT NULL,
    seed               INTEGER NOT NULL,
    clean_garment      INTEGER NOT NULL,
    duration_seconds   REAL NOT NULL
)
"""


@dataclass
class Look:
    """One saved try-on result."""

    id: str
    created: float
    garment_id: int | None
    garment_label: str
    garment_photo_type: str
    steps: int
    seed: int
    clean_garment: bool
    duration_seconds: float


class LookStore:
    """SQLite metadata + PNG files. Safe to use from the API and the job worker thread."""

    def __init__(self, db_path: Path, images_dir: Path):
        self.db_path, self.images_dir = db_path, images_dir
        db_path.parent.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db, db:
            db.execute(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        # A short-lived connection per operation keeps this thread-safe without a lock.
        return sqlite3.connect(self.db_path, timeout=10)

    def image_path(self, look_id: str) -> Path:
        """Where the PNG for a look is stored."""
        return self.images_dir / f"{look_id}.png"

    def add(self, look: Look, png: bytes) -> None:
        """Save a finished try-on: write the image first, so a row never points at nothing."""
        self.image_path(look.id).write_bytes(png)
        row = asdict(look) | {"clean_garment": int(look.clean_garment)}
        cols = ", ".join(row)
        with closing(self._connect()) as db, db:
            db.execute(
                f"INSERT INTO looks ({cols}) VALUES ({', '.join('?' * len(row))})", [*row.values()]
            )

    def get(self, look_id: str) -> Look | None:
        """A look by id, or None."""
        with closing(self._connect()) as db:
            row = db.execute("SELECT * FROM looks WHERE id = ?", (look_id,)).fetchone()
        return self._look(row) if row else None

    def list(self, limit: int = 50) -> list[Look]:
        """Most recent looks first."""
        with closing(self._connect()) as db:
            rows = db.execute(
                "SELECT * FROM looks ORDER BY created DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._look(r) for r in rows]

    def delete(self, look_id: str) -> bool:
        """Delete a look and its image. Returns False if it didn't exist."""
        with closing(self._connect()) as db, db:
            deleted = db.execute("DELETE FROM looks WHERE id = ?", (look_id,)).rowcount
        self.image_path(look_id).unlink(missing_ok=True)
        return bool(deleted)

    def median_duration(self, recent: int = 20) -> float | None:
        """Median try-on time of the most recent looks (for progress estimates), or None."""
        with closing(self._connect()) as db:
            rows = db.execute(
                "SELECT duration_seconds FROM looks ORDER BY created DESC LIMIT ?", (recent,)
            ).fetchall()
        return statistics.median(r[0] for r in rows) if rows else None

    @staticmethod
    def _look(row: tuple) -> Look:
        look = Look(*row)
        look.clean_garment = bool(look.clean_garment)
        return look
