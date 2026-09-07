# 0023: YOLO Format Difference

## Date

2026-08-26

## Lesson

The user asked why YOLO format differs from normal x/y rectangle format.

## Key Insight

Label Studio stores rectangles as top-left x/y plus width/height. YOLO training expects one text row per object with class ID plus normalized center x/y and normalized width/height.

## Practice

- Treat Label Studio JSON as annotation-tool data.
- Treat YOLO TXT as model-training data.
- Convert between them with a small function before writing full dataset files.

## Status

Ready to implement `rectangle_to_yolo` after the format distinction is clear.

