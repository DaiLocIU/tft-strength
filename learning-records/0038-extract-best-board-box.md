# Extract Best Board Box

## Date

2026-08-27

## Context

The user created `scripts/predict_board.py` and printed `results[0].boxes` from Ultralytics.

## Learned

Raw YOLO output is useful for inspection, but app code needs a small typed object. The next useful boundary is `detect_board(image_path: str) -> BoardDetection | None`, where `BoardDetection` contains pixel coordinates and confidence.

## Next Step

Guide the user to define `BoardDetection`, inspect `boxes.xyxy`, `boxes.conf`, and build the first typed return object.
