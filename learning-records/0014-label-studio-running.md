# 0014: Label Studio Running

## Date

2026-08-26

## Lesson

Label Studio was installed into the local project virtual environment and started from the terminal.

## Key Insight

The existing Label Studio project is likely stored in the default Label Studio data directory, so the server was started with the default data directory instead of a fresh project-local data directory.

## Practice

- Open Label Studio at `http://localhost:8081`.
- Find `image_19.png` and `image_33.png`.
- Delete the tiny accidental rectangle in each image.
- Keep the large board rectangle.
- Export JSON again and rerun `scripts/check_dataset.py`.

## Status

Label Studio is running on port 8081. Dataset still needs re-export after fixing duplicate rectangles.

