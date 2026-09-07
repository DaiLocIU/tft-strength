# 0006: JSON Before YOLO

## Date

2026-08-26

## Lesson

For the first export, use Label Studio JSON instead of YOLO.

## Key Insight

YOLO export is useful for direct training, but JSON is better for learning because it exposes the annotation structure that the user will convert by hand.

## Practice

- Export Label Studio data as JSON.
- Save it as `vision-board-detector/exports/label-studio/board-100.json`.
- Inspect the rectangle fields before writing converter code.

## Status

Ready for the first hand-written JSON inspection script after export.

