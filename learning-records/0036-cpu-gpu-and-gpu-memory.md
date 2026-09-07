# CPU GPU And GPU Memory

## Date

2026-08-27

## Context

The user saw `GPU_mem 4.27G` during YOLO training on Mac and asked what CPU, GPU, and GPU memory mean.

## Learned

CPU is a general-purpose processor. GPU is a parallel math processor. Neural network training benefits from GPU because training performs repeated tensor and matrix operations.

On Apple Silicon, PyTorch can use the Apple GPU through the MPS backend with `device=mps`.

`GPU_mem 4.27G` means the training run is using about 4.27 GB of GPU-accessible memory for model weights, batches, intermediate tensors, gradients, and training state.

## Next Step

Teach how `batch`, `imgsz`, and model size affect speed and memory.
