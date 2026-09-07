# When Hex Predictions Still Fail

## Date

2026-08-29

## Context

The user asked what to do if `predict_hex_occupancy` is still wrong after relabeling and retraining,
and whether the process is just labeling and retraining.

## Learned

The main improvement loop is still error-driven labeling and retraining, but only when the remaining
errors are data problems. Each wrong prediction should be categorized as a data problem, threshold
problem, or model-design problem.

Labeling helps when a human can decide the correct class from the crop and the model needs more
examples of that visual pattern. Labeling is not enough when the crop lacks the needed evidence, such
as a champion body spilling into a neighbor hex or a standing point/shadow outside the crop.

## Next Step

For the current model, create a separate mistake queue such as
`data/hex-occupancy/mistakes/v3-wrong.txt`, relabel only those images, rebuild the split, retrain,
and compare. If the same mistake type survives two focused retrains, change a design variable such as
crop size, confidence threshold, uncertain review, neighbor context, or unit anchor detection.
