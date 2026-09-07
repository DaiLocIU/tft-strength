# 0011: Standard Library Before Venv

## Date

2026-08-26

## Lesson

The first dataset verification script can run without a virtual environment because it only uses Python standard-library modules.

## Key Insight

A venv is for project-specific third-party dependencies. It is not required for built-in modules like `json`, `re`, and `pathlib`.

## Practice

- Run `check_dataset.py` with system Python.
- Create a venv later when adding dependencies such as Ultralytics, OpenCV, or Pillow.

## Status

Ready to run the dataset check script after the entry point is added.

