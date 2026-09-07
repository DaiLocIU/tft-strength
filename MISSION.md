# Mission

You want to learn computer vision by building a TFT board detector from scratch.

The practical goal is to take a full Teamfight Tactics screenshot and detect only the playable board area in the UI. This board crop will later become the input for more advanced work, such as champion detection, hex localization, and team strength analysis.

## Current Focus

- Learn the core object detection workflow.
- Use Label Studio for annotation instead of a custom built-in labeler.
- Train a one-class detector where the only class is `board`.
- Keep the first system small enough to understand end to end.

## Not In Scope Yet

- Champion recognition.
- Star-level recognition.
- Hex-by-hex occupancy.
- Full production serving.

