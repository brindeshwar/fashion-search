from pathlib import Path

import pytest

from fashion_search.cli import build_parser


def test_index_command_accepts_paths():
    args = build_parser().parse_args(["index", "--data-dir", "x", "--index-dir", "y"])
    assert args.command == "index"
    assert args.data_dir == Path("x") and args.index_dir == Path("y")


def test_serve_defaults_to_localhost():
    args = build_parser().parse_args(["serve"])
    assert (args.host, args.port) == ("127.0.0.1", 8000)


def test_command_is_required():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_removed_gradio_command_is_rejected():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["app"])
