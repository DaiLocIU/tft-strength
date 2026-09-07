# 0021: Dict Vs Set Return

## Date

2026-08-26

## Lesson

The user returned `{matched, missing, valid_labels, bad_labels}` while the function promised `VerifyResult`.

## Key Insight

In Python, `{value1, value2}` is a set. A `TypedDict` result must use dictionary key-value syntax: `{"matched": matched}`.

## Practice

- Return a dictionary with named keys.
- Add a return type to `find_board_rectangles`.
- Use `result["matched"]` instead of `result.get("matched")` for required fields.

## Status

Ready for the user to fix the two current mypy errors.

