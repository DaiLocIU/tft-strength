# First Hex Occupancy Classifier Smoke Train

## Date

2026-08-28

## Context

The user has split the labeled hex occupancy crops into an Ultralytics-compatible classification
dataset and asked for the next learning step.

## Learned

The next step is a 1-epoch classifier smoke train. This verifies that Ultralytics can load
`data/hex-occupancy`, discover the `occupied` and `empty` classes from folder names, train for one
epoch, and write output artifacts such as `weights/best.pt`.

This is not intended to produce the final model. It is the classification equivalent of the earlier
YOLO board-detector smoke train.

## Next Step

Run:

`.venv/bin/yolo classify train model=yolo11n-cls.pt data=data/hex-occupancy epochs=1 imgsz=96 project=runs/classify name=hex-occupancy-smoke`

Then inspect the generated run folder, especially `weights/best.pt`, `results.csv`, and
`confusion_matrix.png`.
