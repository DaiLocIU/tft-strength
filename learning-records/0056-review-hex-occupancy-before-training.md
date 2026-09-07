# Review Hex Occupancy Before Training

## Date

2026-08-28

## Context

The user labeled many hex occupancy examples and asked for the next required learning step.

## Learned

The labeled dataset now has 776 occupied crops and 2556 empty crops. Before training a classifier,
the user needs to visually review the saved patches. Classification datasets use folder names as
labels, so label quality is entirely controlled by whether each image is in the correct folder.

Training should wait until occupied and empty contact sheets have been reviewed, obvious bad labels
have been fixed, and the dataset has been split into Ultralytics-compatible `train` and `val`
folders.

## Next Step

Create contact sheets for the occupied and empty labeled patch folders, review them visually, then
write a small script to split the reviewed data into `data/hex-occupancy/train` and
`data/hex-occupancy/val`.
