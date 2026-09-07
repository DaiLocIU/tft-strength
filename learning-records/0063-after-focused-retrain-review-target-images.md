# After Focused Retrain Review Target Images

## Date

2026-08-30

## Context

The user relabeled 58 edge-case images, rebuilt the split, retrained the hex occupancy classifier,
copied the new `best.pt` into the active model path, and regenerated all prediction contact sheets.

## Learned

After a focused retrain, the next action is evaluation, not immediate extra labeling. The user should
review the exact images that were in the focused queue first, because those images test whether the
model learned the intended correction.

The decision should be based on the number and type of remaining mistakes. A few remaining mistakes
means the model improved enough to review the broader dataset. Many repeated high-confidence mistakes
with the same cause means one more focused queue may help. If the same cause survives repeated focused
training, the crop or model design should change.

## Next Step

Review only the 58 target images from `data/hex-occupancy/mistakes/new-edge-cases-349-387.txt`.
Record any still-wrong image numbers with a short reason such as `linh thu`, `Blue`, `Maokai`,
`Kayle`, `large champion`, or `low confidence`. Send the remaining wrong list back before relabeling
again.
