# YOLO Line Format

## Date

2026-08-26

## Context

The user converted one Label Studio board rectangle into a typed `YoloRectangle` dictionary and asked how to handle the text line required by YOLO.

## Learned

YOLO label files are plain text. One detected object is represented by one line:

```text
class_id center_x center_y width height
```

The Python conversion should be split into two steps: convert the rectangle data into a typed `YoloRectangle`, then format that object into a string line.

## Next Step

Guide the user to write `yolo_rectangle_to_line(rectangle: YoloRectangle) -> str` and test it on one rectangle before writing files.
