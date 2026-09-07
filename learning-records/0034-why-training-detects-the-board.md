# Why Training Detects The Board

## Date

2026-08-26

## Context

The user asked why training can make a model detect the TFT board.

## Learned

Training compares the model's predicted box against the user's labeled board box. The difference is called loss/error. The trainer repeatedly adjusts the model's internal numbers to reduce that error.

The model learns visual patterns that correlate with the board: the hex grid, board edges, central arena shape, camera angle, and relative screen position.

## Next Step

Teach the user to read loss values in YOLO training output: box loss, class loss, and DFL loss.
