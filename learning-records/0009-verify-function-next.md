# 0009: Verify Function Next

## Date

2026-08-26

## Lesson

The next coding exercise is to write a function that verifies Label Studio tasks match local raw images.

## Key Insight

The function should do one thing only: map each Label Studio image path back to a local raw screenshot and report matched versus missing files.

## Practice

- Create `vision-board-detector/scripts/check_dataset.py`.
- Write `verify_labels_match_images(export_path, raw_dir)`.
- Return `matched` and `missing`.
- Stop after confirming `matched: 100` and `missing: 0`.

## Status

Ready for user-authored code review.

