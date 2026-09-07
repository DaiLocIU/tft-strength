# Review Bottom Row Hex Contact Sheet

## Date

2026-08-27

## Context

The user now has `board-hex-bottom-row-contact-sheet`, which draws seven bottom-row hexes across
all cropped board images.

## Learned

The next skill is visual geometry QA. The user should inspect the contact sheet, decide whether the
row position, height, radius, or border-to-border gap is wrong, then tune only one parameter before
rerunning.

This keeps the feedback loop small before adding staggered rows or all 28 cells.

## Next Step

Have the user tune the bottom row until several random crops look acceptable, then teach the second
row offset.
