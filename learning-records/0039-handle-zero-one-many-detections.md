# Handle Zero One Many Detections

## Date

2026-08-27

## Context

The user asked to write the code that handles zero, one, or multiple board detections and to teach the idea.

## Learned

Inference code must handle all detection counts. No detections returns `None`. One or more detections returns the highest-confidence box using `boxes.conf.argmax()`.

Ultralytics has broad runtime types, so the script uses a small `Any`/`cast` boundary around the model call while keeping the application return type strict.

## Next Step

Move from a script to a reusable function/module that can be called by the main TFT application.
