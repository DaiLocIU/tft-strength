# From Hex Grid To Occupied Hexes

## Date

2026-08-27

## Context

The user has drawn the 4-row, 28-hex board grid and asked what the next step is to detect which hex
has a unit.

## Learned

The next target is hex occupancy, not champion identity. The practical pipeline is: generate hex
polygons, detect generic `unit` boxes, use each unit box's bottom-center point, then assign that
point to the containing hex.

Before training or using a unit detector, the smallest useful coding step is a
`point_is_inside_polygon(...)` function and a typed `HexOccupancy` result.

## Next Step

Teach and implement `point_is_inside_polygon(...)`, then test it with one fake point against the
existing 28 generated hexes.
