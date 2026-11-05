from __future__ import annotations

import json

import pytest

from taskboard.cli import main
from taskboard.core import Task, TaskBoard


def test_export_csv_sorts_numerically_and_uses_lowercase_booleans(
    tmp_path, capsysbinary
) -> None:
    store = tmp_path / "tasks.json"
    store.write_text(
        json.dumps(
            [
                {"id": 10, "title": "ten", "done": False},
                {"id": 2, "title": "中文 😀", "done": True},
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(["--file", str(store), "export", "--format", "csv"])

    assert exit_code == 0
    assert capsysbinary.readouterr().out == (
        "id,title,done\r\n2,中文 😀,true\r\n10,ten,false\r\n".encode("utf-8")
    )


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("a,b", '"a,b"'),
        ('a"b', '"a""b"'),
        ("a\rb", '"a\rb"'),
        ("a\nb", '"a\nb"'),
        ("中文 😀", "中文 😀"),
    ],
)
def test_csv_serializes_special_and_unicode_titles(title: str, expected: str) -> None:
    board = TaskBoard([Task(id=1, title=title)])

    assert board.to_csv() == f"id,title,done\r\n1,{expected},false\r\n"


def test_export_csv_empty_board_ends_with_crlf(tmp_path, capsysbinary) -> None:
    store = tmp_path / "tasks.json"
    store.write_text("[]", encoding="utf-8")

    exit_code = main(["--file", str(store), "export", "--format", "csv"])

    assert exit_code == 0
    assert capsysbinary.readouterr().out == b"id,title,done\r\n"


def test_export_csv_missing_store_is_an_empty_board(tmp_path, capsysbinary) -> None:
    store = tmp_path / "missing.json"

    exit_code = main(["--file", str(store), "export", "--format", "csv"])

    assert exit_code == 0
    assert capsysbinary.readouterr().out == b"id,title,done\r\n"


def test_export_rejects_unknown_format_without_stdout(tmp_path, capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--file", str(tmp_path / "tasks.json"), "export", "--format", "json"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert captured.out == ""
    assert "invalid choice" in captured.err


@pytest.mark.parametrize("contents", ["{not json", '{"not": "a list"}'])
def test_export_invalid_store_reports_error_without_csv(
    tmp_path, capsysbinary, contents: str
) -> None:
    store = tmp_path / "tasks.json"
    store.write_text(contents, encoding="utf-8")

    exit_code = main(["--file", str(store), "export", "--format", "csv"])

    captured = capsysbinary.readouterr()
    assert exit_code == 2
    assert b"invalid store" in captured.err
    assert captured.out == b""
