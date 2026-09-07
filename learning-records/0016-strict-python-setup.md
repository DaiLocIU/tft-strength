# 0016: Strict Python Setup

## Date

2026-08-26

## Lesson

The user wants Python to feel more like TypeScript. The project now has strict type-checking configuration.

## Key Insight

Python strictness comes from tooling layered on top of Python: type hints, mypy or pyright, and a linter such as ruff.

## Practice

- Add type hints to one function at a time.
- Run mypy to check types.
- Run ruff to catch style and likely bugs.
- Keep the config aligned with the venv's Python version.

## Status

`pyproject.toml` and `pyrightconfig.json` were added. The venv currently uses Python 3.9.6.

