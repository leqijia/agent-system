"""Tasks are small Markdown files in `project/tasks/`. Git is the database."""

from __future__ import annotations

import re
from pathlib import Path

from labkit.config import Config, LabError

STATUSES = ("todo", "doing", "review", "done", "dropped")

TEMPLATE = """# {task_id}: {title}

Status: todo

## Goal

<One or two sentences: what should be true when this is finished, and why it matters.>

## Done when

<A command that passes or a result someone can observe. Example: `uv run pytest tests/test_x.py`
passes, or `uv run lab run experiments/specs/x.toml` reports loss below 0.01.>

## Scope

- May change: <files or folders>
- Must not change: <files or folders, e.g. tests/acceptance, experiments/specs>

## Notes

<Context the agent cannot see in the code: decisions, links, dead ends already tried.>

## Log

<Appended by whoever works on the task: date, what was done, what was learned.>
"""


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40] or "task"


def all_tasks(cfg: Config) -> list[dict]:
    tasks = []
    for path in sorted(cfg.path("tasks").glob("T[0-9][0-9][0-9][0-9]-*.md")):
        text = path.read_text()
        title = re.search(r"^# (T\d{4}): (.*)$", text, re.M)
        status = re.search(r"^Status:\s*(\w+)", text, re.M)
        tasks.append(
            {
                "id": path.name[:5],
                "title": title.group(2) if title else path.stem,
                "status": status.group(1) if status else "todo",
                "path": path,
            }
        )
    return tasks


def find(cfg: Config, task_id: str) -> dict:
    for task in all_tasks(cfg):
        if task["id"] == task_id.upper():
            return task
    raise LabError(f"no task {task_id} in {cfg.path('tasks')}")


def new(cfg: Config, title: str) -> Path:
    numbers = [int(t["id"][1:]) for t in all_tasks(cfg)]
    task_id = f"T{max(numbers, default=0) + 1:04d}"
    folder = cfg.path("tasks")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{task_id}-{_slug(title)}.md"
    path.write_text(TEMPLATE.format(task_id=task_id, title=title))
    return path


def set_status(cfg: Config, task_id: str, status: str) -> Path:
    if status not in STATUSES:
        raise LabError(f"status must be one of {STATUSES}")
    task = find(cfg, task_id)
    text = task["path"].read_text()
    updated, count = re.subn(r"^Status:.*$", f"Status: {status}", text, count=1, flags=re.M)
    if not count:
        raise LabError(f"{task['path'].name} has no 'Status:' line")
    task["path"].write_text(updated)
    return task["path"]
