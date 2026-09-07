# 0004: Board Labeling Rule

## Date

2026-08-26

## Lesson

The user is labeling 100 TFT screenshots in Label Studio with one rectangle label: `board`.

## Key Insight

The important skill at this stage is consistent semantic labeling. A model cannot learn a stable board detector if the human definition of `board` changes across screenshots.

## Practice

- Label 10 screenshots first.
- Review the 10 labels before continuing.
- Exclude bench, shop, side panels, top UI, and champion-specific boxes.
- Continue to 100 only after the boundary rule feels stable.

## Status

Labeling guidance added. Next learning step is inspecting a small Label Studio JSON export.

