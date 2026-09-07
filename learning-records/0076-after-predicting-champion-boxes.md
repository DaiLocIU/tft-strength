# After Predicting Champion Boxes

The user has replaced `vision-board-detector/models/champion-detector.pt` with the newest detector
and predicted boxes for all `399` board crops.

The next correct step is to use those boxes as a source for champion identity crops, then label each
crop by champion name. Whole board crops should not be used directly to train champion identity,
because the classifier input should be one champion crop.

The user should continue with this order:

1. Review predicted champion boxes.
2. Use `scripts/label_champion_identity.py` to crop and label champion names.
3. Fix typo folders under `data/champion-identity/labeled`.
4. Run `scripts/split_champion_identity_dataset.py`.
5. Train `yolo classify train` on `data/champion-identity`.
6. Later connect classifier output back to the chosen hex.

Star-level detection remains a later step after champion identity works.
