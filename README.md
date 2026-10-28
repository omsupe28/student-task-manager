# Student Task Manager

A simple Python application for a concept-based assignment. Add study tasks, track due dates and priorities, mark work complete, and view progress. Data is saved locally in JSON.

## Requirements

- Python 3.10 or newer
- A terminal (PowerShell, Command Prompt, Terminal, or a similar shell)
- No third-party Python packages

## Run the application

Open a terminal in this folder. Use `python3` instead of `python` if that is how Python is available on your computer.

```sh
python task_manager.py --help
python task_manager.py add "Finish Python report" --due 2026-11-05 --priority high
python task_manager.py add "Revise functions" --priority medium
python task_manager.py list
python task_manager.py list --status pending
python task_manager.py complete 1
python task_manager.py summary
python task_manager.py delete 2
```

The application creates `task_data.json` alongside the script after the first change. Each command reloads the saved file. To use a different file, put `--data` before the command:

```sh
python task_manager.py --data practice.json add "Practice loops"
python task_manager.py --data practice.json list
```

Use a path inside a temporary folder for experiments. The default personal task data is excluded from Git; do not add custom data files to a public repository.

## Concepts demonstrated

| Python concept | Use in the application |
| --- | --- |
| Variables and data types | IDs, titles, priorities, dates, and Boolean completion flags |
| Lists and dictionaries | A task collection and individual task records |
| Functions | Separate loading, saving, validation, and task operations |
| Conditions and loops | Command routing, task lookup, listing, and validation |
| File handling and JSON | Persistent storage between runs |
| Exception handling | Readable errors for invalid data or file access failures |
| Standard library modules | argparse, datetime, pathlib, json, tempfile, and unittest |

## Tests

```sh
python -m unittest -v
```

The test suite uses temporary files and does not modify your personal task file. It checks persistence, validation, completion, filtering, deletion, progress calculations, corrupted data, failed writes, and the full command workflow.

## Files

- `task_manager.py`: application and command-line entry point
- `test_task_manager.py`: automated tests
- `docs/assignment_report.pdf`: four-page assignment report
- `docs/assignment_report.md`: editable report text
- `.gitignore`: excludes runtime files and personal task data
- `.gitattributes`: preserves source line endings and treats PDFs as binary files

## Limitations

This is a local, single-user application. It has no reminders, graphical interface, user accounts, or synchronization. Concurrent edits from separate processes are unsupported. Delete removes a task immediately; there is no undo. Due dates are stored and displayed without automatic scheduling or overdue alerts.

## GitHub repository

[View the repository](https://github.com/omsupe28/student-task-manager) or read the [final assignment report](docs/assignment_report.pdf). The report includes the project design, Python concepts, a recorded demonstration, and test results.
