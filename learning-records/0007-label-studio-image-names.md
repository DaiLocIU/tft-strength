# 0007: Label Studio Image Names

## Date

2026-08-26

## Lesson

Label Studio JSON exports may reference uploaded images using internal paths and hash-prefixed filenames.

## Key Insight

The JSON path `/data/upload/1/0992a392-image_2.png` belongs to the original local screenshot `image_2.png`. The converter can recover the original filename by stripping the hash prefix.

## Practice

- Keep original screenshots in `vision-board-detector/data/raw/`.
- Use the JSON `data.image` field to identify each task.
- Do not train until the image path mapping is understood.

## Status

Ready to write the first manual Python script that loads JSON and prints image mappings.

