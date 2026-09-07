# After First Good Detections

## Date

2026-08-26

## Context

The user got strong board predictions after training 20 epochs and asked what to do next in both good-result and bad-result cases.

## Learned

The next step is broad prediction review, not immediate more training. A good single screenshot proves the model can learn the concept, but the model must be tested across many raw screenshots.

Good results lead to a real train/validation split and integration code. Bad results should be classified by failure type: no box, many boxes, wrong area, bench included, or failure on unseen images.

## Next Step

Run prediction over `data/raw`, inspect the generated images, and list failure filenames by category.
