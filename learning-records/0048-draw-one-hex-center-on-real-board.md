# Draw One Hex Center On Real Board

## Date

2026-08-27

## Context

The user pointed out that it is hard to know if generated hex geometry is correct without drawing
on a real board image.

## Learned

The next learning step should bring visual feedback earlier. Instead of building all 28 hexes
first, draw one `HexCell` center as a red dot on `outputs/board-crops/image_1.png`.

This makes geometry tuning concrete: adjust `center_x` to move left/right and `center_y` to move
up/down.

## Next Step

Have the user write `create_first_hex_cell()` and `draw_hex_center(...)`, then run the script and
inspect `outputs/hex-overlays/one-center.png`.
