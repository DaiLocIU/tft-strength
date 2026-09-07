# Start Hex Grid From Empty Code

## Date

2026-08-27

## Context

The generated `detect_hexes.py` moved too fast and became hard for the user to reason about. The
user asked to remove it and rebuild the hex detector step by step.

## Learned

The first step in hex detection is not drawing polygons. It is defining the typed data shape for one
hex cell: row, column, center x, and center y.

This keeps the learning focused and lets later steps build from a simple, testable structure.

## Next Step

Guide the user to recreate `scripts/detect_hexes.py` manually with only the `HexCell` `TypedDict`,
then run mypy and ruff.
