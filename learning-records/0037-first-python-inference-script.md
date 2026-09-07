# First Python Inference Script

## Date

2026-08-27

## Context

The user copied the trained board detector into a stable model path: `vision-board-detector/models/board-detector.pt`.

## Learned

After training, the next phase is inference code. The CLI is useful for experiments, but the application needs Python code that loads the model and returns board coordinates.

The first script should inspect raw Ultralytics prediction results before wrapping them in a clean `detect_board` function.

## Next Step

Guide the user to create `scripts/predict_board.py`, load `YOLO("models/board-detector.pt")`, run prediction on one raw image, and print boxes/confidence.
