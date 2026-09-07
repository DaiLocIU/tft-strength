# Label Units On Board Crops

## Date

2026-08-27

## Context

The board detector and batch crop pipeline are good enough to move to the next visual target.

## Learned

The next detector should find generic `unit` boxes on cropped board images. This should happen
before champion identity detection, because location is simpler than classification.

The user should label only visible units on the board, excluding bench units, shop cards, and the
Little Legend unless a separate class is intentionally added later.

## Next Step

Create a new Label Studio project for board crops, label 30 to 50 images with one `unit` class,
export JSON, and reuse the existing Label Studio-to-YOLO conversion pattern for the new dataset.
