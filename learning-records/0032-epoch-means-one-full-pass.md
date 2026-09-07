# Epoch Means One Full Pass

## Date

2026-08-26

## Context

The user asked why the first YOLO train used `epochs=1` and the next recommendation used `epochs=20`.

## Learned

An epoch is one full pass through the training dataset. With 100 images, `epochs=1` means YOLO sees the 100 images once. `epochs=20` means it sees them twenty times.

The first one-epoch run was a smoke test for the dataset pipeline. A longer run is the first real learning test.

## Next Step

Run a 20-epoch train, then predict one image and inspect whether the board box appears cleanly.
