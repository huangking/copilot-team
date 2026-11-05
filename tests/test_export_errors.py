from __future__ import annotations

import pytest

from taskboard.cli import main


def test_export_rejects_missing_format_without_stdout(tmp_path, capsysbinary) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--file", str(tmp_path / "tasks.json"), "export"])

    captured = capsysbinary.readouterr()
    assert exc_info.value.code == 2
    assert captured.out == b""
    assert b"--format" in captured.err


@pytest.mark.parametrize("contents", ["", "null", "42", '"tasks"'])
def test_export_rejects_invalid_store_without_stdout(
    tmp_path, capsysbinary, contents: str
) -> None:
    store = tmp_path / "tasks.json"
    store.write_text(contents, encoding="utf-8")

    exit_code = main(["--file", str(store), "export", "--format", "csv"])

    captured = capsysbinary.readouterr()
    assert exit_code == 2
    assert b"invalid store" in captured.err
    assert captured.out == b""
