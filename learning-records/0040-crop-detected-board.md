# Crop Detected Board

## Date

2026-08-27

## Context

The user has a working `detect_board` function that returns a typed `BoardDetection` with pixel coordinates and confidence.

## Learned

The next useful step is cropping the detected board region from the full screenshot. This converts model output into an image region that later champion/unit analysis can use.

Cropping should use the detected `x1`, `y1`, `x2`, and `y2` coordinates, converted to integers.

## Next Step

Guide the user to add Pillow and write `crop_board(image_path, detection, output_path) -> None`.
