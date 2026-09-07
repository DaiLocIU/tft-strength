# Combine Hex Occupancy With Champion Map

The user clarified that the hex occupancy classifier should remain in the pipeline, with champion
box-to-hex mapping used as a second signal rather than a replacement. The next implementation step
is `combine_hex_signals.py`, which should compare occupancy and champion-map evidence per
`(row, column)` and draw disagreement for review.
