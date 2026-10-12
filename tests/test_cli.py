from pathlib import Path

import pytest

from fashion_search.cli import build_parser


def test_index_command_accepts_paths():
    args = build_parser().parse_args(["index", "--data-dir", "x", "--index-dir", "y"])
    assert args.command == "index"
    assert args.data_dir == Path("x") and args.index_dir == Path("y")


def test_app_default_port():
    assert build_parser().parse_args(["app"]).port == 7860


def test_command_is_required():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_app_ui_builds_without_loading_model(catalog):
    from fashion_search.app import build_app

    assert build_app(catalog) is not None
