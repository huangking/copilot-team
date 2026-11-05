from __future__ import annotations

import json

from taskboard.cli import main


def test_add_then_list_persists_to_the_store(tmp_path, capsys) -> None:
    store = tmp_path / "tasks.json"

    assert main(["--file", str(store), "add", "write spec"]) == 0
    assert main(["--file", str(store), "add", "implement"]) == 0
    assert main(["--file", str(store), "list"]) == 0

    out = capsys.readouterr().out
    assert "[ ] #1 write spec" in out
    assert "[ ] #2 implement" in out
    assert json.loads(store.read_text()) == [
        {"id": 1, "title": "write spec", "done": False},
        {"id": 2, "title": "implement", "done": False},
    ]


def test_done_updates_the_store(tmp_path) -> None:
    store = tmp_path / "tasks.json"
    main(["--file", str(store), "add", "one"])

    assert main(["--file", str(store), "done", "1"]) == 0
    assert main(["--file", str(store), "list", "--status", "done"]) == 0

    rows = json.loads(store.read_text())
    assert rows[0]["done"] is True


def test_missing_task_reports_an_error_and_nonzero_exit(tmp_path, capsys) -> None:
    store = tmp_path / "tasks.json"

    assert main(["--file", str(store), "done", "42"]) == 2

    captured = capsys.readouterr()
    assert "error: task 42 not found" in captured.err
    assert captured.out == ""


def test_invalid_store_is_reported_instead_of_crashing(tmp_path, capsys) -> None:
    store = tmp_path / "tasks.json"
    store.write_text("{not json")

    assert main(["--file", str(store), "list"]) == 2

    assert "invalid store" in capsys.readouterr().err
