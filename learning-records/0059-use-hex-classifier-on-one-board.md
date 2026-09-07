# Use Hex Classifier On One Board

## Date

2026-08-28

## Context

The user successfully ran the first hex occupancy classifier smoke train and asked for the next
learning step.

## Learned

The 1-epoch classifier smoke run produced `best.pt` and reached about 97.0% top-1 validation
accuracy. The confusion matrix had 527 true empty predicted empty, 10 true empty predicted occupied,
10 true occupied predicted empty, and 125 true occupied predicted occupied.

The next step is not more training by default. The next useful step is inference: load the classifier
model, crop each generated hex patch from one board crop, predict `empty` or `occupied`, and draw the
predicted occupied hexes on the board image.

## Next Step

Implement `scripts/predict_hex_occupancy.py` using the classifier at
`runs/classify/runs/classify/hex-occupancy-smoke/weights/best.pt`, then test on one board crop and
save a review overlay image.
