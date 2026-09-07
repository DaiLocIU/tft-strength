# 0001: One-Class Board Detector

## Date

2026-08-26

## Lesson

The first computer vision target is a one-class object detector for the TFT board.

## Key Insight

Detecting the board first reduces the problem size. Later champion detection can run inside the board crop instead of scanning the whole screenshot.

## Practice

- Create or collect raw screenshots.
- Label one `board` rectangle per screenshot in Label Studio.
- Export annotations.
- Convert the export into YOLO format.
- Train and test a small detector.

## Status

Project scaffold created. User still needs to add screenshots, label them, and run the first training pass.

