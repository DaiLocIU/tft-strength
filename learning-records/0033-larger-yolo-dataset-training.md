# Larger YOLO Dataset Training

## Date

2026-08-26

## Context

The user asked how training changes with a larger dataset.

## Learned

With a larger dataset, the main change is a real train/validation split. `val` should no longer point to `images/train`; it should point to `images/val` so model quality is measured on screenshots it did not directly train on.

Training settings such as `epochs`, `batch`, `imgsz`, and `device` should be adjusted based on dataset size and machine speed.

## Next Step

Teach the user to split the current 100 images into train and val folders before continuing to serious training.
