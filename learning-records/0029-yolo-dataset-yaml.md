# YOLO Dataset YAML

## Date

2026-08-26

## Context

The user fixed the YOLO folder layout. The project now has 100 PNG files in `data/yolo/images/train`, 100 TXT label files in `data/yolo/labels/train`, and 0 PNG files in the labels folder.

## Learned

Ultralytics needs a dataset YAML file that maps the dataset root, train image folder, validation image folder, and class names.

For the first smoke test, `val` can temporarily point at `images/train`; later it should become a real validation split.

## Next Step

Create `data/yolo/dataset.yaml`, then run a lightweight training smoke test once Ultralytics is installed.
