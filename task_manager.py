"""A small, dependency-free command-line application for student tasks."""

import argparse
from datetime import date
import json
import os
from pathlib import Path
import tempfile


PRIORITIES = ("low", "medium", "high")
DEFAULT_DATA = Path(__file__).resolve().with_name("task_data.json")


def validate_due(value):
    """Accept an empty date or a real calendar date in YYYY-MM-DD format."""
    if value == "":
        return value
    if not isinstance(value, str):
        raise ValueError("Due date must be text in YYYY-MM-DD format.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("Due date must be a real date in YYYY-MM-DD format.") from error
    if parsed.isoformat() != value:
        raise ValueError("Due date must use YYYY-MM-DD format.")
    return value


def validate_title(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Task title cannot be empty.")
    value = value.strip()
    if len(value) > 120 or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError("Task title must be one line of at most 120 characters.")
    return value


def load_data(path):
    """Validate stored data before any operation can modify it."""
    path = Path(path)
    if not path.exists():
        return {"next_id": 1, "tasks": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError("Cannot read task data. Keep the file and repair it or use --data with a new path.") from error
    if not isinstance(data, dict) or set(data) != {"next_id", "tasks"}:
        raise ValueError("Task data must contain next_id and tasks.")
    if type(data["next_id"]) is not int or data["next_id"] < 1 or not isinstance(data["tasks"], list):
        raise ValueError("Task data has an invalid next_id or task list.")
    seen = set()
    for task in data["tasks"]:
        if not isinstance(task, dict) or set(task) != {"id", "title", "due", "priority", "completed"}:
            raise ValueError("Task data contains an invalid task record.")
        task_id = task["id"]
        if type(task_id) is not int or task_id < 1 or task_id in seen:
            raise ValueError("Task IDs must be unique positive integers.")
        seen.add(task_id)
        if validate_title(task["title"]) != task["title"]:
            raise ValueError("Stored task titles must not have surrounding whitespace.")
        validate_due(task["due"])
        if task["priority"] not in PRIORITIES or type(task["completed"]) is not bool:
            raise ValueError("Task data has an invalid priority or completion status.")
    if seen and data["next_id"] <= max(seen):
        raise ValueError("The next task ID must be greater than every stored ID.")
    return data


def save_data(path, data):
    """Replace the old JSON only after the new contents have been written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def add_task(data, title, due="", priority="medium"):
    title = validate_title(title)
    due = validate_due(due)
    if priority not in PRIORITIES:
        raise ValueError("Priority must be low, medium, or high.")
    task = {"id": data["next_id"], "title": title, "due": due,
            "priority": priority, "completed": False}
    data["tasks"].append(task)
    data["next_id"] += 1
    return task


def find_task(data, task_id):
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task
    raise ValueError(f"Task {task_id} was not found.")


def complete_task(data, task_id):
    task = find_task(data, task_id)
    task["completed"] = True
    return task


def delete_task(data, task_id):
    task = find_task(data, task_id)
    data["tasks"].remove(task)
    return task


def list_tasks(data, status="all"):
    return [task for task in data["tasks"]
            if status == "all" or task["completed"] == (status == "completed")]


def summarize(data):
    total = len(data["tasks"])
    completed = sum(task["completed"] for task in data["tasks"])
    return {"total": total, "completed": completed, "pending": total - completed,
            "percent": round(100 * completed / total, 1) if total else 0.0}


def build_parser():
    parser = argparse.ArgumentParser(description="Keep track of student assignments and study tasks.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA,
                        help="JSON file location; place this option before the command")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="Add a task")
    add.add_argument("title", help="Task title (quote titles containing spaces)")
    add.add_argument("--due", default="", help="Optional due date as YYYY-MM-DD")
    add.add_argument("--priority", choices=PRIORITIES, default="medium")
    listing = commands.add_parser("list", help="Show tasks")
    listing.add_argument("--status", choices=("all", "pending", "completed"), default="all")
    for name, help_text in (("complete", "Mark a task complete"), ("delete", "Delete a task")):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("id", type=int, help="Task ID shown by list")
    commands.add_parser("summary", help="Show task counts and completion percentage")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        data = load_data(args.data)
        if args.command == "add":
            task = add_task(data, args.title, args.due, args.priority)
            save_data(args.data, data)
            print(f"Added task {task['id']}: {task['title']}")
        elif args.command == "list":
            tasks = list_tasks(data, args.status)
            if not tasks:
                print("No tasks found.")
            for task in tasks:
                status = "done" if task["completed"] else "pending"
                print(f"{task['id']:>3} | {status:7} | {task['priority']:6} | "
                      f"{task['due'] or 'no date':10} | {task['title']}")
        elif args.command == "complete":
            task = complete_task(data, args.id)
            save_data(args.data, data)
            print(f"Completed task {task['id']}: {task['title']}")
        elif args.command == "delete":
            task = delete_task(data, args.id)
            save_data(args.data, data)
            print(f"Deleted task {task['id']}: {task['title']}")
        else:
            result = summarize(data)
            print(f"Total: {result['total']} | Completed: {result['completed']} | "
                  f"Pending: {result['pending']} | Progress: {result['percent']:.1f}%")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
