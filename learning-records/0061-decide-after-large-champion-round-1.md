# Decide After Large Champion Round 1

## Date

2026-08-29

## Context

The user finished labeling 48 large-champion mistake images, trained, predicted again, and asked for
the next required step.

## Learned

The latest corrected dataset has 1279 occupied and 3817 empty examples. The large-champion round
training produced a strong validation result: 1133 true empty predicted empty, 25 true empty
predicted occupied, 14 true occupied predicted empty, and 396 true occupied predicted occupied.

The next decision should be based on the confidence of remaining wrong red hexes. If most wrong red
hexes are low confidence, raise the occupied threshold before labeling more. If wrong red hexes are
high confidence, create another focused mistake queue and retrain.

## Next Step

Review the latest prediction contact sheets and record remaining wrong image names. If the wrong red
hexes are mostly around 0.50 to 0.75 confidence, test a stricter occupied threshold such as 0.75 in
`scripts/predict_hex_occupancy.py`.
