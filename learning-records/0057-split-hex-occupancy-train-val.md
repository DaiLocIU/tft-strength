# Split Hex Occupancy Train Val

## Date

2026-08-28

## Context

The user has generated occupied and empty contact sheets and asked for the next learning step.

## Learned

The next step after visual review is to split the labeled hex occupancy patches into a classifier
dataset with `train` and `val` folders. `train` is used for learning; `val` is held back to check
whether the model works on examples it did not train on.

The split should happen by original board image, not by individual patch, because patches from the
same board share visual context. Mixing patches from the same source board into both train and val
would make validation too easy.

## Next Step

Implement `scripts/split_hex_occupancy_dataset.py` to copy reviewed labeled patches into
`data/hex-occupancy/train/{occupied,empty}` and `data/hex-occupancy/val/{occupied,empty}`, grouped
by source image name with an 80/20 split.
