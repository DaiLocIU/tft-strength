# Understand First YOLO Train Output

## Date

2026-08-26

## Context

The user ran the first Ultralytics YOLO smoke training successfully and saw `runs/detect/train`, but did not understand the output.

## Learned

The first run proves the training pipeline can read the dataset and produce a model file. It should not be judged for accuracy because it used one epoch and a temporary train-as-val setup.

The key artifact is `weights/best.pt`, which can now be used for prediction on a screenshot.

## Next Step

Run YOLO prediction with `best.pt` on one image and inspect whether the drawn box is around the TFT board.
