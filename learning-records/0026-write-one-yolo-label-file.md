# Write One YOLO Label File

## Date

2026-08-26

## Context

The user successfully created and printed one YOLO label line from a Label Studio rectangle.

## Learned

The next step is not full dataset export yet. The next step is writing one YOLO line into one `.txt` file whose base name matches the image file.

Example:

```text
image_1.png -> image_1.txt
```

## Next Step

Guide the user to implement `write_yolo_label_file(image_filename, yolo_line, labels_dir) -> None` and manually inspect the created file.
