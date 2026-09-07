# Freeze A Board State Output

The user reports that the current board result is good. The next step should be to turn the visual
overlay into a stable JSON board-state output.

The recommended next milestone is:

1. Keep the current detector, identity classifier, and hex occupancy classifier.
2. Add JSON output under `vision-board-detector/outputs/board-state`.
3. Export one record per occupied champion hex.
4. Include `row`, `column`, `champion`, `identity_confidence`, `champion_box_confidence`, and
   `source`.
5. Add an identity confidence gate around `0.70` so weak names become `unknown`.
6. Verify several hard boards by comparing review images to JSON.

Star-level detection should come after the board-state JSON contract is stable.
