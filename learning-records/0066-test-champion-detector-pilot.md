# Test The Champion Detector Pilot

## Date

2026-08-31

## Context

The user trained a one-class champion detector pilot and copied the trained weight into
`vision-board-detector/models/champion-detector.pt`. The user asked what to do next after training.

## Learned

After a detector trains successfully, the next step is not automatic retraining. The next step is
visual prediction review. For this project, the detector must be judged by whether it detects real
champion bodies and ignores little legends, item effects, health bars, and board background.

The champion detector is currently an evidence source, not the final hex answer. If prediction
overlays look useful, the next coding step is to combine champion boxes with known hex centers and
debug the box-to-hex mapping visually.

## Next Step

Run YOLO prediction on `data/champion-detector/images/val` using
`models/champion-detector.pt`, inspect the saved images in `outputs/champion-detector/pilot-val`,
and list the important mistakes. Move to box-to-hex mapping only if the pilot detects most champion
bodies and mostly ignores little legends/effects.
