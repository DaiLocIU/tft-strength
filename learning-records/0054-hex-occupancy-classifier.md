# Hex Occupancy Classifier

## Date

2026-08-28

## Context

The user decided that four board-corner detection may not improve alignment enough and asked whether
to move directly to detecting which hexes have champions.

## Learned

The next task should be hex occupancy classification, not champion recognition. Since the project
already generates hex positions, each hex can become a small image crop. A classifier can then answer
whether that crop is `occupied` or `empty`.

This differs from object detection: detection predicts object boxes, while classification chooses one
label for one already-cropped image. For Ultralytics classification datasets, class folder names such
as `occupied` and `empty` become the labels.

## Next Step

Write a small `crop_hex_patch(...)` function that crops one square patch around a hex center, then
generate a contact sheet of patches for visual review before training any classifier.
