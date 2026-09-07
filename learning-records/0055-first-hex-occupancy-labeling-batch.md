# First Hex Occupancy Labeling Batch

## Date

2026-08-28

## Context

The user has a tiny browser tool for labeling occupied hexes on cropped TFT boards and asked what
the next required step is.

## Learned

The next required step is data creation, not training. The user should label a small batch first:
about 30 board crops using the current 28-cell player-side grid. Since most hexes are empty, the
tool defaults cells to `empty`, and the user only clicks cells where a champion is standing.

This first batch is a quality gate. Before training, the saved classifier patches must be reviewed to
make sure `occupied` images usually contain champions and `empty` images usually contain board
texture only.

## Next Step

After labeling 30 board crops, create a contact sheet from
`vision-board-detector/data/hex-occupancy/labeled/occupied` and
`vision-board-detector/data/hex-occupancy/labeled/empty` so the labels and patch size can be checked
visually.
