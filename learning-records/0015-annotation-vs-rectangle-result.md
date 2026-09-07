# 0015: Annotation Vs Rectangle Result

## Date

2026-08-26

## Lesson

Label Studio's table annotation count is not the same as the number of rectangles inside that annotation.

## Key Insight

One task can have one submitted annotation, and that annotation can contain multiple `result` items. For this project, each task should have one annotation object containing exactly one `board` rectangle result.

## Practice

- Open `image_19.png` and `image_33.png` in the labeling detail view.
- Select the tiny rectangle result.
- Delete only the tiny rectangle.
- Keep the large board rectangle.
- Save/update the annotation, then export JSON again.

## Status

User should edit rectangle results in detail view, not rely on the table annotation count.

