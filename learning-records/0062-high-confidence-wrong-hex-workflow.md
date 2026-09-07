# High Confidence Wrong Hex Workflow

## Date

2026-08-29

## Context

The user asked what actually to do when a wrong hex has high confidence: record it, or immediately
label again.

## Learned

For high-confidence wrong hexes, the user should first record the board image number while reviewing
prediction sheets. They should collect a focused batch, usually 20 to 50 wrong images, then create a
mistake queue and relabel that queue. Retraining after each single image is inefficient.

High confidence means the model strongly learned the wrong visual pattern, so threshold changes are
unlikely to fix the error. Corrected examples of the same mistake type are needed. If the same
high-confidence mistake survives two focused retrain rounds, the crop/model design should change.

## Next Step

While reviewing prediction contact sheets, record image numbers for high-confidence wrong red hexes.
After collecting a focused batch, create a new mistake queue, relabel the queue, rebuild the split,
train again, and predict all again.
