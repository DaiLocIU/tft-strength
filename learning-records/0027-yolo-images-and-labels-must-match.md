# YOLO Images And Labels Must Match

## Date

2026-08-26

## Context

The user wrote YOLO label files successfully. The project now has 100 `.txt` files under `data/yolo/labels/train`.

## Learned

YOLO needs image files and label files in parallel folders. The base filename must match:

```text
images/train/image_1.png
labels/train/image_1.txt
```

## Next Step

Guide the user to write `copy_yolo_image_file(image_filename, raw_dir, images_dir) -> None`, then verify image count and label count match.
