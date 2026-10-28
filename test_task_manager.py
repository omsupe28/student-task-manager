"""Behavior checks using only Python's standard library."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import task_manager as app


class TaskManagerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "tasks.json"
        self.data = app.load_data(self.path)

    def test_missing_file_starts_empty(self):
        self.assertEqual(self.data, {"next_id": 1, "tasks": []})
        self.assertFalse(self.path.exists())

    def test_add_and_reload(self):
        app.add_task(self.data, "  Finish report  ", "2026-11-05", "high")
        app.save_data(self.path, self.data)
        loaded = app.load_data(self.path)
        self.assertEqual(loaded, self.data)
        self.assertEqual(loaded["tasks"][0]["title"], "Finish report")

    def test_empty_title_is_rejected(self):
        with self.assertRaises(ValueError):
            app.add_task(self.data, "  ")
        self.assertEqual(self.data["next_id"], 1)

    def test_long_or_multiline_title_is_rejected(self):
        for title in ("x" * 121, "first\nsecond"):
            with self.subTest(title=title), self.assertRaises(ValueError):
                app.add_task(self.data, title)

    def test_invalid_dates_are_rejected(self):
        for due in ("2026-02-30", "05-11-2026", "20261105", None):
            with self.subTest(due=due), self.assertRaises(ValueError):
                app.add_task(self.data, "Study", due)

    def test_invalid_priority_is_rejected(self):
        with self.assertRaises(ValueError):
            app.add_task(self.data, "Study", priority="urgent")

    def test_completion_and_filters(self):
        app.add_task(self.data, "Read")
        app.add_task(self.data, "Write")
        app.complete_task(self.data, 1)
        self.assertEqual([t["id"] for t in app.list_tasks(self.data, "pending")], [2])
        self.assertEqual([t["id"] for t in app.list_tasks(self.data, "completed")], [1])

    def test_repeated_completion_is_safe(self):
        app.add_task(self.data, "Read")
        app.complete_task(self.data, 1)
        app.complete_task(self.data, 1)
        self.assertEqual(app.summarize(self.data)["completed"], 1)

    def test_deleted_ids_are_not_reused(self):
        app.add_task(self.data, "First")
        app.delete_task(self.data, 1)
        self.assertEqual(app.add_task(self.data, "Second")["id"], 2)

    def test_unknown_ids_are_rejected(self):
        for operation in (app.complete_task, app.delete_task):
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation(self.data, 99)

    def test_summary_handles_empty_and_nonempty_lists(self):
        self.assertEqual(app.summarize(self.data)["percent"], 0.0)
        app.add_task(self.data, "Read")
        app.add_task(self.data, "Write")
        app.complete_task(self.data, 1)
        self.assertEqual(app.summarize(self.data),
                         {"total": 2, "completed": 1, "pending": 1, "percent": 50.0})

    def test_malformed_json_is_preserved(self):
        self.path.write_text("{broken", encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            app.main(["--data", str(self.path), "add", "Study"])
        self.assertEqual(error.exception.code, 1)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{broken")

    def test_invalid_schema_is_rejected(self):
        invalid = [[], {"next_id": True, "tasks": []}, {"next_id": 1, "tasks": [None]}]
        for data in invalid:
            self.path.write_text(json.dumps(data), encoding="utf-8")
            with self.subTest(data=data), self.assertRaises(ValueError):
                app.load_data(self.path)

    def test_duplicate_ids_and_bad_counter_are_rejected(self):
        task = app.add_task(self.data, "Read")
        self.data["tasks"].append(dict(task))
        app.save_data(self.path, self.data)
        with self.assertRaises(ValueError):
            app.load_data(self.path)
        self.data["tasks"].pop()
        self.data["next_id"] = 1
        app.save_data(self.path, self.data)
        with self.assertRaises(ValueError):
            app.load_data(self.path)

    def test_failed_replace_keeps_original_file(self):
        app.save_data(self.path, self.data)
        original = self.path.read_bytes()
        app.add_task(self.data, "Read")
        with patch("task_manager.os.replace", side_effect=OSError("Write failed")):
            with self.assertRaises(OSError):
                app.save_data(self.path, self.data)
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_cli_workflow_and_persistence(self):
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture):
            for command in (["add", "Study", "--priority", "high"], ["list"],
                            ["complete", "1"], ["summary"], ["delete", "1"], ["list"]):
                self.assertEqual(app.main(["--data", str(self.path)] + command), 0)
        self.assertIn("Progress: 100.0%", capture.getvalue())
        self.assertIn("No tasks found.", capture.getvalue())
        self.assertEqual(app.load_data(self.path)["tasks"], [])


if __name__ == "__main__":
    unittest.main()
