# 0008: Raw Images Match Export

## Date

2026-08-26

## Lesson

The user copied raw images into `vision-board-detector/data/raw`, and the Label Studio export now matches local files.

## Key Insight

Before converting annotations, verify file identity. A correct annotation is useless to training if the converter cannot locate the matching image.

## Practice

- Read `task["data"]["image"]`.
- Extract the Label Studio internal filename.
- Strip the hash prefix to recover the original filename.
- Check whether that file exists in `data/raw`.

## Status

100 labeled tasks matched 100 local images. Ready for the user to write `scripts/check_dataset.py`.

