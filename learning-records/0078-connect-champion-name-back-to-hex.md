# Connect Champion Name Back To Hex

The user has trained and copied `models/champion-identity-classifier.pt` with `71` classes. The
next learning step is to connect classifier output back into the existing combined hex pipeline.

Existing code in `scripts/combine_hex_signals.py` already maps each champion box to one chosen hex.
The missing bridge is:

1. Load `models/champion-identity-classifier.pt`.
2. Crop the same champion box that was mapped to the hex.
3. Run the classifier on that crop at `imgsz=160`.
4. Store `champion_name` and `identity_confidence` in the champion evidence.
5. Print and draw `row,column + champion_name`.

The user should not add star-level detection yet. Star level should wait until `hex + champion name`
works end to end.
