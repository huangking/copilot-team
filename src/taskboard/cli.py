"""Command line entry point.

Persistence is a single JSON file (`.taskboard.json` by default) next to the
user; there is no database and no network access.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import TaskBoard, TaskError

DEFAULT_STORE = Path(".taskboard.json")


def load_board(path: Path) -> TaskBoard:
    if not path.exists():
        return TaskBoard()
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TaskError(f"invalid store {path}: {exc}") from exc
    if not isinstance(rows, list):
        raise TaskError(f"invalid store {path}: expected a list")
    return TaskBoard.from_dicts(rows)


def save_board(path: Path, board: TaskBoard) -> None:
    path.write_text(
        json.dumps(board.to_dicts(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="taskboard", description="A tiny task board")
    parser.add_argument("--file", type=Path, default=DEFAULT_STORE, help="JSON store path")
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add", help="add a task")
    add.add_argument("title")

    listing = commands.add_parser("list", help="list tasks")
    listing.add_argument("--status", choices=["all", "open", "done"], default="all")

    done = commands.add_parser("done", help="mark a task as done")
    done.add_argument("id", type=int)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        board = load_board(args.file)
        if args.command == "add":
            task = board.add(args.title)
            save_board(args.file, board)
            print(f"added #{task.id} {task.title}")
        elif args.command == "list":
            for task in board.list(args.status):
                mark = "x" if task.done else " "
                print(f"[{mark}] #{task.id} {task.title}")
        elif args.command == "done":
            task = board.complete(args.id)
            save_board(args.file, board)
            print(f"done #{task.id} {task.title}")
    except TaskError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0
