# 0017: First Strict Checks

## Date

2026-08-26

## Lesson

Strict Python tooling is installed and reports useful feedback on the user's first dataset script.

## Key Insight

Mypy strict mode behaves like TypeScript's `noImplicitAny`: it requires function annotations instead of allowing untyped function boundaries.

## Practice

- Add type annotations to `verify_labels_match_images`.
- Add type annotations to `find_board_rectangles`.
- Fix Ruff's long line and unnecessary f-string.
- Re-run mypy and ruff.

## Status

Script works at runtime, but strict checks are not clean yet.

