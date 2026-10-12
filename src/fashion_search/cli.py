"""Command-line entry point: ``fashion-search {index,app,evaluate}``."""

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


if __name__ == "__main__":
    main()
