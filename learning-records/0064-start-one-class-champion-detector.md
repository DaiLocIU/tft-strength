# Start One-Class Champion Detector

## Date

2026-08-31

## Context

The user found that the hex occupancy classifier still makes mistakes when large champions, Blue,
Nunu, Kayle, Ivern, Elder Dragon, Maokai, item effects, and little legends overlap nearby hexes. The
user decided that pure retraining is not a satisfying long-term fix and asked for the next step to
detect champions.

## Learned

The next model should be a one-class object detector with the class `champion`. It should detect full
champion bodies on board crops, not classify champion names yet. One champion should have one box,
even if the body overlaps multiple hexes.

The detector is useful because it turns one visual unit into one object. Later, the bottom-center of
each champion box can be mapped to the nearest hex center to estimate the standing hex.

## Next Step

Create a first champion detector dataset from 30 to 50 board crops. Select hard images with Blue,
Nunu, Kayle, Ivern, Elder Dragon, Maokai, and large overlap cases, but label every visible
player-side champion in each selected image. Do not label little legends, item effects alone, empty
hexes, or enemy-side champions for the first player-side detector.
