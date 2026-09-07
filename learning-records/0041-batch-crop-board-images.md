# Batch Crop Board Images

## Date

2026-08-27

## Context

The user successfully cropped one detected TFT board from one screenshot using
`detect_board` plus `crop_board`.

## Learned

The next project step is batch processing: loop through `data/raw/*.png`, detect the board in each
image, save successful crops into `outputs/board-crops`, and record failures in a typed result.

This shifts the project from a one-image demo into a reusable computer vision pipeline.

## Next Step

Guide the user to write `crop_all_boards(raw_dir: str, output_dir: str) -> BatchCropSummary`, then
optionally add a `--all` CLI mode to `scripts/predict_board.py`.
