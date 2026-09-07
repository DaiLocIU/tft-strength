# Train The First Champion Name Model

The user is ready to move from champion box detection to champion name classification.

Current checked state:

- `data/champion-identity/labeled` has hundreds of labeled crop images.
- `data/champion-identity/train` and `data/champion-identity/val` do not exist yet.
- `models/champion-identity-classifier.pt` does not exist yet.

The next concrete workflow is:

1. Review label folder names for typos because folder names become class labels.
2. Run `scripts/split_champion_identity_dataset.py`.
3. Train with `yolo classify train`, not `yolo detect train`.
4. Copy `runs/classify/champion-identity/weights/best.pt` to
   `models/champion-identity-classifier.pt`.
5. Test the classifier on validation crops before wiring it back into the board-to-hex pipeline.

The important distinction is that `champion-detector.pt` detects boxes from a board crop, while
`champion-identity-classifier.pt` predicts one name from one champion crop.
