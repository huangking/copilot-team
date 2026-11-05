from __future__ import annotations

import json

import pytest

from taskboard.cli import main
from taskboard.core import Task, TaskBoard


def test_export_csv_quotes_title_with_combined_crlf_and_delimiters(
    tmp_path, capsysbinary
) -> None:
    store = tmp_path / "tasks.json"
    store.write_text(
        json.dumps([{"id": 1, "title": 'first,\r\nsay "hello"', "done": False}]),
        encoding="utf-8",
    )

    exit_code = main(["--file", str(store), "export", "--format", "csv"])

    captured = capsysbinary.readouterr()
    assert exit_code == 0
    assert captured.out == (
        b'id,title,done\r\n1,"first,\r\nsay ""hello""",false\r\n'
    )


def test_export_csv_empty_title_stays_an_empty_field() -> None:
    board = TaskBoard([Task(id=1, title="")])

    assert board.to_csv() == "id,title,done\r\n1,,false\r\n"


def test_export_rejects_missing_format_without_output(tmp_path, capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--file", str(tmp_path / "tasks.json"), "export"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert captured.out == ""
    assert "--format" in captured.err


@pytest.mark.parametrize("contents", ["", "null", '"not a list"', "42"])
def test_export_non_list_store_values_report_error_without_csv(
    tmp_path, capsysbinary, contents: str
) -> None:
    store = tmp_path / "tasks.json"
    store.write_text(contents, encoding="utf-8")

    exit_code = main(["--file", str(store), "export", "--format", "csv"])

    captured = capsysbinary.readouterr()
    assert exit_code == 2
    assert b"invalid store" in captured.err
    assert captured.out == b""
