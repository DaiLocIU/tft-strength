# Create First Row Of Hex Centers

## Date

2026-08-27

## Context

The user wants to rebuild hex detection manually after removing the generated script.

## Learned

The next useful geometry step is one row of 7 hex centers. In a single row, `center_y` stays fixed,
while `center_x` is calculated as `start_x + column * gap`.

This teaches the core spacing formula before adding staggered rows, perspective, or drawing.

## Next Step

Have the user write `create_hex_row(...) -> list[HexCell]`, print the first row, and verify that it
returns 7 cells.
