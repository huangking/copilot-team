"""Taskboard domain logic.

No I/O in this module: the CLI owns persistence and printing. Keeping the
domain pure is what makes it cheap to test and safe for an agent to modify.
"""

from __future__ import annotations

from dataclasses import dataclass


class TaskError(ValueError):
    """Raised when a task operation is invalid."""


@dataclass(slots=True)
class Task:
    """A single task. `id` is assigned by the board and never reused."""

    id: int
    title: str
    done: bool = False

    def to_dict(self) -> dict[str, object]:
        return {"id": self.id, "title": self.title, "done": self.done}


class TaskBoard:
    """In-memory task board; one instance is also the unit of persistence."""

    def __init__(self, tasks: list[Task] | None = None) -> None:
        self._tasks: list[Task] = list(tasks or ())
        self._next_id = max((task.id for task in self._tasks), default=0) + 1

    def add(self, title: str) -> Task:
        """Add a task with a trimmed, non-empty title."""
        title = title.strip()
        if not title:
            raise TaskError("title must not be empty")
        task = Task(id=self._next_id, title=title)
        self._next_id += 1
        self._tasks.append(task)
        return task

    def get(self, task_id: int) -> Task:
        for task in self._tasks:
            if task.id == task_id:
                return task
        raise TaskError(f"task {task_id} not found")

    def complete(self, task_id: int) -> Task:
        task = self.get(task_id)
        task.done = True
        return task

    def list(self, status: str = "all") -> list[Task]:
        if status == "all":
            return list(self._tasks)
        if status == "open":
            return [task for task in self._tasks if not task.done]
        if status == "done":
            return [task for task in self._tasks if task.done]
        raise TaskError(f"unknown status: {status}")

    def to_dicts(self) -> list[dict[str, object]]:
        return [task.to_dict() for task in self._tasks]

    @classmethod
    def from_dicts(cls, rows: list[dict[str, object]]) -> "TaskBoard":
        tasks = [
            Task(
                id=int(row["id"]),
                title=str(row["title"]),
                done=bool(row.get("done", False)),
            )
            for row in rows
        ]
        return cls(tasks)
