from __future__ import annotations

import pytest

from taskboard.core import Task, TaskBoard, TaskError


def test_add_assigns_increasing_ids_and_trims_title() -> None:
    board = TaskBoard()
    first = board.add("  write spec  ")
    second = board.add("ship it")

    assert first.id == 1
    assert first.title == "write spec"
    assert second.id == 2
    assert not first.done


@pytest.mark.parametrize("title", ["", "   ", "\n\t"])
def test_add_rejects_blank_titles(title: str) -> None:
    with pytest.raises(TaskError, match="title must not be empty"):
        TaskBoard().add(title)


def test_complete_marks_task_done() -> None:
    board = TaskBoard()
    task = board.add("write tests")

    done = board.complete(task.id)

    assert done is task
    assert done.done is True


def test_complete_missing_task_raises() -> None:
    with pytest.raises(TaskError, match="task 99 not found"):
        TaskBoard().complete(99)


def test_list_filters_by_status() -> None:
    board = TaskBoard()
    first = board.add("one")
    second = board.add("two")
    third = board.add("three")
    board.complete(first.id)
    board.complete(third.id)

    assert [task.id for task in board.list()] == [1, 2, 3]
    assert [task.id for task in board.list("open")] == [second.id]
    assert [task.id for task in board.list("done")] == [first.id, third.id]


def test_list_rejects_unknown_status() -> None:
    with pytest.raises(TaskError, match="unknown status: late"):
        TaskBoard().list("late")


def test_round_trip_preserves_tasks_and_next_id() -> None:
    board = TaskBoard()
    board.add("one")
    board.add("two")
    board.complete(1)

    restored = TaskBoard.from_dicts(board.to_dicts())
    next_task = restored.add("three")

    assert next_task.id == 3
    assert [task.to_dict() for task in restored.list()] == [
        {"id": 1, "title": "one", "done": True},
        {"id": 2, "title": "two", "done": False},
        {"id": 3, "title": "three", "done": False},
    ]


def test_from_dicts_tolerates_legacy_rows_without_done() -> None:
    board = TaskBoard.from_dicts([{"id": 7, "title": "legacy"}])

    assert board.list()[0] == Task(id=7, title="legacy", done=False)
