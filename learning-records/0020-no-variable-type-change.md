# 0020: No Variable Type Change

## Date

2026-08-26

## Lesson

Strict mypy rejected assigning `Path` values back into parameters typed as `str`.

## Key Insight

In strict Python, keep one variable name tied to one type. Convert values into new local variables such as `export_file = Path(export_path)`.

## Practice

- Replace `export_path = Path(export_path)` with `export_file = Path(export_path)`.
- Replace `raw_dir = Path(raw_dir)` with `raw_path = Path(raw_dir)`.
- Return a `VerifyResult` dictionary instead of a tuple.
- Add a return type to `find_board_rectangles`.

## Status

Ready for the user to edit `scripts/check_dataset.py` and rerun mypy.

