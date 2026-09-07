# Label Four Board Corners

## Date

2026-08-28

## Context

The user changed direction from manually tuning hex centers from a rectangular board crop to
detecting the four playable-board corners and using perspective transform.

## Learned

The next task should be a separate YOLO pose/keypoint dataset, not a replacement for the existing
rectangle detector. The existing detector can still create rough board crops. The new labels should
represent one `board` object with four ordered keypoints: `top_left`, `top_right`, `bottom_right`,
and `bottom_left`.

Label Studio should use `KeyPointLabels` with stable `model_index` values and a parent
`RectangleLabels` board box for YOLO keypoint export.

## Next Step

Have the user create a small Label Studio project using the four-corner config and label 20 rough
board crops before writing a Label Studio JSON to YOLO pose converter.
