# 0012: Ready To Validate Label Structure

## Date

2026-08-26

## Lesson

The dataset image matching step passed with 100 matched and 0 missing images.

## Key Insight

Before converting labels to YOLO, verify the annotation structure. Each labeled task should contain exactly one rectangle labeled `board`.

## Practice

- Add `find_board_rectangles(task)` to `scripts/check_dataset.py`.
- Count tasks with exactly one board rectangle.
- Report valid and bad label counts.

## Status

Ready for user-authored label structure validation.

