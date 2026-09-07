# Run A Tiny Champion Detector Pilot

## Date

2026-08-31

## Context

The user questioned whether champion detection will work because champions are often hidden by other
champions, with left, right, and bottom parts occluded. The user asked for the actual next step.

## Learned

The champion detector should not be treated as a guaranteed replacement for hex occupancy. A box
bottom-center heuristic can fail. The detector should first be tested as an additional evidence
source: rough object location, object count, and rejection of false positives from large body overlap,
little legends, and effects.

The safest next step is a tiny pilot, not a full labeling campaign. Label 10 to 15 hard board crops,
train a small detector, and inspect whether detections are useful on the known wrong cases.

## Next Step

Create a Label Studio project named `champion-detector-pilot`. Import 10 to 15 board crops from hard
images such as `image_4.png`, `image_6.png`, `image_77.png`, `image_99.png`, `image_237.png`,
`image_263.png`, `image_264.png`, `image_265.png`, `image_371.png`, `image_382.png`, and
`image_383.png`. Use one class, `champion`, and label every clearly visible player-side champion.
Then stop and train a tiny detector before labeling more.
