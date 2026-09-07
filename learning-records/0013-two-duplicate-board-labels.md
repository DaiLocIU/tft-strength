# 0013: Two Duplicate Board Labels

## Date

2026-08-26

## Lesson

The user's validation script runs, but its `board_annotations: 100` output counted tasks, not tasks with exactly one valid board rectangle.

## Key Insight

Dataset validation must ask the training-specific question. For this one-class detector, each task needs exactly one `board` rectangle.

## Practice

- Improve `find_board_rectangles` to safely return board rectangle values.
- Count valid tasks where `len(rectangles) == 1`.
- Print bad tasks where the count is not one.
- Fix duplicate labels for `image_19.png` and `image_33.png`.

## Status

Actual dataset state: 98 valid tasks, 2 tasks with duplicate board rectangles.

