"""Command-line entry point: ``fashion-search {index,app,evaluate,tryon,tryon-download}``."""

import argparse
from pathlib import Path

from . import __version__
from .config import DATA_DIR, INDEX_DIR


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fashion-search", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_index = sub.add_parser("index", help="Embed and tag every image in the data folder")
    p_index.add_argument("--data-dir", type=Path, default=DATA_DIR)
    p_index.add_argument("--index-dir", type=Path, default=INDEX_DIR)

    p_app = sub.add_parser("app", help="Launch the Gradio web UI")
    p_app.add_argument("--data-dir", type=Path, default=DATA_DIR)
    p_app.add_argument("--index-dir", type=Path, default=INDEX_DIR)
    p_app.add_argument("--port", type=int, default=7860)

    sub.add_parser("evaluate", help="Compare the 2025 MLP with zero-shot FashionSigLIP")

    sub.add_parser("tryon-download", help="Download virtual try-on weights (~2 GB)")

    p_tryon = sub.add_parser("tryon", help="Put a garment on a person photo")
    p_tryon.add_argument("--person", type=Path, required=True)
    p_tryon.add_argument("--garment", type=Path, required=True)
    p_tryon.add_argument("--out", type=Path, default=Path("tryon.png"))
    p_tryon.add_argument("--category", choices=["tops", "bottoms", "one-pieces"], default="tops")
    p_tryon.add_argument("--garment-photo-type", choices=["flat-lay", "model"], default="flat-lay")
    p_tryon.add_argument("--steps", type=int, default=30)
    p_tryon.add_argument("--seed", type=int, default=42)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    # Heavy imports (torch, gradio) are deferred so `--help` stays instant.
    if args.command == "index":
        from .indexing import build_index

        build_index(args.data_dir, args.index_dir)
    elif args.command == "app":
        from .app import launch
        from .catalog import Catalog

        launch(Catalog.load(args.index_dir, args.data_dir), port=args.port)
    elif args.command == "evaluate":
        from .evaluate import run_evaluation

        run_evaluation()
    elif args.command == "tryon-download":
        from .tryon import download_weights

        download_weights()
    elif args.command == "tryon":
        from PIL import Image

        from .tryon import try_on

        result = try_on(
            Image.open(args.person),
            Image.open(args.garment),
            args.category,
            args.garment_photo_type,
            args.steps,
            args.seed,
        )
        result.save(args.out)
        print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
