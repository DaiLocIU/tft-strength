# Balance Missed Champions And Wrong Names

The user reports that the latest champion-name result is better, and wrong names mostly occur below
about `0.70` identity confidence. However, using `--champion-conf 0.65` causes some real champions
to be missed.

The next concept is separating two thresholds:

- `champion-conf` controls detector recall. If too high, real champion boxes disappear.
- `identity-conf` controls name trust. If too low, weak guessed names are shown as facts.

Recommended next step:

1. Lower detector confidence to around `0.50` to recover missing champion boxes.
2. Add or use an identity confidence gate around `0.70` or `0.75`.
3. Treat missing boxes as a detector dataset problem.
4. Treat weak or wrong names on existing boxes as an identity dataset problem.

The user should not try to fix missing champion boxes by adding more identity labels. Identity labels
only help after a champion box exists.
