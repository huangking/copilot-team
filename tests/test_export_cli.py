from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_cli(store: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "taskboard",
            "--file",
            str(store),
            "export",
            *arguments,
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        check=False,
    )


def test_cli_exports_sorted_csv_as_utf8_with_rfc4180_quoting(tmp_path) -> None:
    store = tmp_path / "tasks.json"
    store.write_text(
        json.dumps(
            [
                {"id": 10, "title": "中文 😀", "done": False},
                {"id": 2, "title": 'a,\r\n"quoted"', "done": True},
            ]
        ),
        encoding="utf-8",
    )

    result = _run_cli(store, "--format", "csv")

    assert result.returncode == 0, f"stderr={result.stderr!r}"
    assert result.stdout == (
        'id,title,done\r\n2,"a,\r\n""quoted""",true\r\n10,中文 😀,false\r\n'
    ).encode("utf-8"), f"unexpected stdout: {result.stdout!r}"
    assert result.stderr == b"", f"unexpected stderr: {result.stderr!r}"


@pytest.mark.parametrize("contents", ["[]", None])
def test_cli_exports_only_header_for_empty_or_missing_store(tmp_path, contents) -> None:
    store = tmp_path / "tasks.json"
    if contents is not None:
        store.write_text(contents, encoding="utf-8")

    result = _run_cli(store, "--format", "csv")

    assert result.returncode == 0, f"stderr={result.stderr!r}"
    assert result.stdout == b"id,title,done\r\n", (
        f"expected header-only CRLF output, got {result.stdout!r}"
    )
    assert result.stderr == b"", f"unexpected stderr: {result.stderr!r}"


def test_cli_rejects_unknown_format_without_stdout(tmp_path) -> None:
    result = _run_cli(tmp_path / "tasks.json", "--format", "json")

    assert result.returncode == 2, f"expected exit 2, got {result.returncode}"
    assert result.stdout == b"", f"unexpected stdout: {result.stdout!r}"
    assert b"invalid choice" in result.stderr, (
        f"expected format validation error, got {result.stderr!r}"
    )


def test_cli_requires_format_without_stdout(tmp_path) -> None:
    result = _run_cli(tmp_path / "tasks.json")

    assert result.returncode == 2, f"expected exit 2, got {result.returncode}"
    assert result.stdout == b"", f"unexpected stdout: {result.stdout!r}"
    assert b"--format" in result.stderr, (
        f"expected required-format error, got {result.stderr!r}"
    )


@pytest.mark.parametrize("contents", ["{not json", '{"not": "a list"}'])
def test_cli_reports_invalid_store_without_csv(tmp_path, contents: str) -> None:
    store = tmp_path / "tasks.json"
    store.write_text(contents, encoding="utf-8")

    result = _run_cli(store, "--format", "csv")

    assert result.returncode == 2, f"expected exit 2, got {result.returncode}"
    assert result.stdout == b"", f"unexpected stdout: {result.stdout!r}"
    assert b"invalid store" in result.stderr, (
        f"expected invalid-store error, got {result.stderr!r}"
    )
