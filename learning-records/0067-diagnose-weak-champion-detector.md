# Diagnose A Weak Champion Detector

## Date

2026-08-31

## Context

The user's champion detector produced no visible boxes at normal confidence, but produced many wrong
boxes across the whole map at very low confidence. The user asked for the next step to handle this
current case.

## Learned

When a YOLO detector predicts nothing at `conf=0.25` but many random boxes at `conf=0.01`, the model
has weak guesses rather than useful detections. The immediate next step is diagnosis, not pipeline
integration.

The important test is to run prediction on the training images. If training images also fail, the
problem is likely export, labels, training setup, or undertraining. If training images work but
validation images fail, the dataset is too small or not varied enough.

## Next Step

Run prediction on `data/champion-detector/images/train` with `conf=0.25`. If the train images show
good champion boxes, label about 50 more hard board crops. If train images still show no boxes,
inspect Label Studio export and YOLO label files before adding more data.
