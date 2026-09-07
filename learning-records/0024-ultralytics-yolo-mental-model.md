# Ultralytics YOLO Mental Model

## Date

2026-08-26

## Context

The user asked what Ultralytics YOLO is while preparing to train a one-class TFT board detector from Label Studio labels.

## Learned

Ultralytics YOLO is both a YOLO model family and a Python/CLI toolkit. For this project, it is the trainer and predictor that will learn the `board` bounding box from prepared images and YOLO-format label files.

The user does not need to write the neural network from scratch yet. The next learning target is the full data loop: images, labels, dataset layout, training, prediction, and mistake inspection.

## Next Step

Teach the YOLO dataset folder layout and `dataset.yaml`, then guide the user to convert one Label Studio rectangle into one YOLO label line.
