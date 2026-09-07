# Missed Champions Need Failure Focused Data

The user clarified that the 100 epoch champion detector misses many real champions on board crops
at `conf=0.5`. The correct next teaching step is to build a labeling batch from missed detections
and retrain, not to move into box-to-hex mapping yet.
