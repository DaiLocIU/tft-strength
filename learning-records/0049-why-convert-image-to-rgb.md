# Why Convert Image To RGB

## Date

2026-08-27

## Context

The user asked why the drawing code uses `Image.open(image_path).convert("RGB")`.

## Learned

`Image.open` preserves the image file's current pixel mode, such as RGB, RGBA, palette, or
grayscale. `convert("RGB")` normalizes the image to three color channels before drawing overlays.

For the user's hex overlay workflow, RGB makes drawing red dots, white labels, and saved review
images predictable.

## Next Step

Continue with `draw_hex_center(...)`: open a board crop, convert to RGB, draw one red center point,
save a review image, and visually inspect whether the point is correct.
