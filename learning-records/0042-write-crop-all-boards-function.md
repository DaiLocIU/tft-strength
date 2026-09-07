# Write crop_all_boards Function

## Date

2026-08-27

## Context

The user has a working one-image crop path and wants to write the batch function manually for
learning.

## Learned

`crop_all_boards` should be a pipeline function: convert folder strings to `Path` values, create
typed result lists, loop through sorted `.png` files, call `detect_board`, skip failures with
`continue`, reuse `crop_board` for successes, and return a `BatchCropSummary`.

The function should report failures instead of hiding them, because failed screenshots become the
next labeling/training candidates.

## Next Step

After the user writes the function, run mypy and runtime-test it. Then decide whether to add a
proper `--all` CLI mode.
