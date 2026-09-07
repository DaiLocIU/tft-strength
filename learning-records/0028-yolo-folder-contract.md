# YOLO Folder Contract

## Date

2026-08-26

## Context

The user added image copying after generating YOLO label files. The script passed mypy, but the default `images_dir` pointed at `data/yolo/labels/train`.

## Learned

Static typing can prove that a value is a string, but it cannot prove that the string points to the correct semantic folder. YOLO dataset folders have a contract:

```text
images/train/*.png
labels/train/*.txt
```

The same base filename connects an image to its label.

## Next Step

Fix the `images_dir` default, remove accidentally copied PNG files from `labels/train`, rerun the script, and verify file counts.
