# Review Board Crops With Contact Sheet

## Date

2026-08-27

## Context

The user implemented batch board cropping. The latest run cropped 343 images and failed on 5:
`image_10.png`, `image_11.png`, `image_12.png`, `image_300.png`, and `image_338.png`.

## Learned

The next step after cropping is visual quality control. A successful crop count is not enough,
because the model may still crop too much, too little, or the wrong region.

A contact sheet lets the user scan many board crops quickly and identify bad examples by filename.

## Next Step

Guide the user to create `create_contact_sheet(crops_dir, output_path, columns, thumb_width)`, using
Pillow to resize crop images, paste them into a grid, and draw filenames below each thumbnail.
