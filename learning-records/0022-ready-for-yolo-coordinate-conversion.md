# 0022: Ready For YOLO Coordinate Conversion

## Date

2026-08-26

## Lesson

The user's dataset verification now passes: 100 matched images and 100 valid board labels.

## Key Insight

The next computer vision skill is coordinate conversion: Label Studio stores top-left percentage boxes, while YOLO expects normalized center-based boxes.

## Practice

- Write `rectangle_to_yolo(rectangle: RectangleValue) -> str`.
- Convert one rectangle before writing the full dataset converter.
- Use the known example `x=10`, `y=20`, `width=50`, `height=40`.

## Status

Ready for user-authored one-rectangle YOLO conversion.

