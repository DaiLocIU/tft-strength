# AI / Machine Learning Learning Roadmap

This roadmap uses **TFT Strength** as the main hands-on project for learning AI, machine learning, PyTorch, computer vision, and later video/sequence modeling in depth.

The goal is not only to use pretrained libraries, but to understand **why models work, how to train/evaluate them, why they fail, and how to improve them**.

---

## Long-term product direction

Current V1:

```text
Screenshot
→ board detection
→ champion detection / classification
→ OCR player stats
→ structured TFT board state
```

Future direction:

```text
High-rank TFT videos
→ extract game states over time
→ infer player actions
→ build a dataset of state → action → outcome
→ compare user decisions with strong-player decisions
→ generate evidence-based recommendations
```

The recommendation system should eventually use structured game-state data and learned patterns, with an LLM used mainly to explain recommendations rather than make unsupported decisions.

---

# Phase 1 — Machine Learning Fundamentals

## Learn

- Supervised vs unsupervised learning
- Features and labels
- Training / validation / test split
- Overfitting and underfitting
- Bias vs variance
- Parameters vs hyperparameters
- Loss functions
- Regularization
- Class imbalance
- Data leakage
- Cross-validation
- Precision, recall, F1-score
- Confusion matrix
- ROC / AUC

## TFT practice

Use the champion/star/occupancy datasets to answer questions such as:

- Are some champion classes under-represented?
- Does training accuracy increase while validation accuracy stops improving?
- Which champions are most frequently confused?
- How does blur, crop, brightness, or resolution affect accuracy?

## Milestone

Be able to explain why a model performs badly using training/validation evidence instead of only saying "the model is inaccurate".

---

# Phase 2 — Math for Deep Learning

Focus on understanding concepts rather than formal proofs first.

## Linear algebra

- Scalars, vectors, matrices, tensors
- Dot product
- Matrix multiplication
- Transpose
- Vector norms
- Linear transformations

## Calculus

- Derivatives
- Partial derivatives
- Gradients
- Chain rule
- Gradient descent

## Probability / statistics

- Mean and variance
- Probability distributions
- Conditional probability
- Expectation
- Sampling

## TFT practice

Implement small examples with PyTorch tensors and manually inspect how changing a weight changes the loss.

## Milestone

Understand conceptually:

```text
input
→ model
→ prediction
→ loss
→ gradient
→ parameter update
```

---

# Phase 3 — PyTorch Deep Dive

Do not depend only on high-level wrappers such as `YOLO.train()`.

## Core PyTorch

Learn:

- `torch.Tensor`
- tensor shapes and dimensions
- dtype
- CPU vs GPU
- indexing / slicing
- broadcasting
- `reshape`, `view`, `permute`
- matrix multiplication
- `requires_grad`
- autograd
- `.backward()`
- `.grad`

## Neural-network APIs

Learn:

- `nn.Module`
- `forward()`
- model parameters
- loss functions
- optimizers
- `Dataset`
- `DataLoader`
- batches
- epochs
- `model.train()` / `model.eval()`
- checkpoints

## Build manually

Create a champion identity classifier without Ultralytics:

```text
champion crop
→ custom PyTorch CNN
→ champion class
```

Write the full training loop yourself:

```python
for images, labels in train_loader:
    optimizer.zero_grad()
    logits = model(images)
    loss = criterion(logits, labels)
    loss.backward()
    optimizer.step()
```

Then write validation/evaluation code separately.

## Experiments

Compare:

- SGD vs Adam
- different learning rates
- batch sizes
- augmentations
- training from scratch vs transfer learning

## Milestone

Be able to build, train, validate, save, load, and debug a PyTorch classifier without a training framework.

---

# Phase 4 — Deep Learning Fundamentals

## Learn deeply

- Neurons
- Weights and bias
- Activation functions
- ReLU
- Sigmoid
- Softmax
- Forward pass
- Loss functions
- Backpropagation
- Gradient descent
- SGD / Adam
- Learning rate
- Batch size
- Epochs
- Weight initialization
- Dropout
- Normalization
- Vanishing / exploding gradients

## Important exercise

Implement a very small network and inspect gradients after:

```python
loss.backward()
```

Understand which parameters receive gradients and why.

---

# Phase 5 — Computer Vision Fundamentals

## Image representation

Learn:

- Width / height / channels
- RGB
- Image tensors
- Normalization
- Resize / interpolation
- Data augmentation

## CNN concepts

Learn:

- Convolution
- Kernels / filters
- Feature maps
- Channels
- Stride
- Padding
- Pooling
- Receptive field

## Architectures to study

Understand the important ideas behind:

- LeNet
- AlexNet
- VGG
- ResNet
- EfficientNet

Do not memorize architectures. Focus on why architectural changes were introduced.

Example: understand why **ResNet skip connections** help deeper networks train.

## TFT practice

Use champion identity and star classification to experiment with CNN architectures and transfer learning.

---

# Phase 6 — Object Detection and YOLO Internals

Because TFT Strength already uses YOLO, learn what is happening underneath the API.

## Learn

- Bounding boxes
- IoU
- Confidence score
- Classification score
- Localization loss
- Classification loss
- Precision / recall for detection
- mAP@0.5
- mAP@0.5:0.95
- Non-Maximum Suppression (NMS)
- Anchor-based vs anchor-free detection

## YOLO conceptual pipeline

```text
image
→ backbone
→ feature extraction
→ neck
→ multi-scale features
→ detection head
→ box/class predictions
→ NMS
```

## Implement manually

At least once:

- Calculate IoU yourself
- Implement a simple NMS function
- Evaluate precision/recall from prediction results

## TFT experiments

Investigate questions such as:

- Does resize resolution hurt small champion detection?
- Is low recall caused by missing detections or confidence threshold?
- Which board positions have weaker localization?
- How does augmentation affect mAP?

## Milestone

Move from:

> YOLO is inaccurate.

To explanations such as:

> Recall is low on small champions after image resizing, while precision remains high, so the model is missing objects rather than producing many false positives.

---

# Phase 7 — Build a TFT Video State Pipeline

Do this before trying to build recommendations.

## Learn

- FFmpeg basics
- OpenCV video processing
- Frame extraction
- Frame sampling
- Timestamp handling
- Image-difference / scene-change detection

A 30 FPS, 30-minute video contains roughly 54,000 frames, so avoid running heavy inference on every frame.

Instead detect meaningful changes such as:

- Round starts / ends
- Board changes
- Shop changes
- Gold changes
- Item changes

## V2 milestone

```text
TFT video
→ identify rounds
→ extract representative frames
→ run current CV pipeline
→ create match timeline
```

Example:

```text
2-1 → GameState
2-2 → GameState
2-3 → GameState
...
6-1 → GameState
```

---

# Phase 8 — Object Tracking and State Transitions

## Learn

- Tracking-by-detection
- SORT concepts
- ByteTrack
- DeepSORT concepts

For TFT, board cells can simplify tracking because units occupy structured locations.

## State model

Create a clear representation such as:

```text
GameState
- stage
- round
- hp
- gold
- level
- xp
- streak
- board units
- bench units
- shop
- items
- traits
- augments
```

And units:

```text
Unit
- champion_id
- star_level
- items
- board_position
```

## Infer actions from state differences

Instead of detecting every mouse click, infer actions from transitions:

```text
state_before
+ detected differences
→ inferred action
→ state_after
```

Possible actions:

- BUY
- SELL
- LEVEL_UP
- REFRESH
- MOVE_UNIT
- BENCH_UNIT
- EQUIP_ITEM
- SELECT_AUGMENT

## V3 milestone

Create a structured sequence:

```text
state_1 → action_1
state_2 → action_2
state_3 → action_3
```

---

# Phase 9 — Recommendation Data and Similarity Search

Do not assume every action from a Top-1 player is automatically correct.

Store:

```text
state
→ action
→ immediate outcome
→ eventual placement
```

Useful outcome fields:

- round win/loss
- HP change
- board strength
- economy
- final placement

## State similarity

Learn embeddings and nearest-neighbor search.

Potential tools:

- pgvector (preferred first because the project already uses PostgreSQL/Supabase)
- FAISS
- Qdrant

Example:

```text
user state
→ find similar high-rank states
→ inspect actions taken
→ compare outcomes
```

Possible recommendation:

> In similar Stage 4-2 states, strong players usually leveled to 8 instead of rolling at level 7.

## V4 milestone

Build recommendations from historical evidence before training a complex neural recommendation model.

---

# Phase 10 — Sequential Models and Transformers

Only start this after the structured timeline/data pipeline is reliable.

## Learn

- Sequence modeling
- RNN concepts
- LSTM concepts
- Embeddings
- Attention
- Query / Key / Value
- Self-attention
- Positional encoding
- Transformer encoder
- Vision Transformer (ViT)
- Temporal / video transformers

A TFT match can eventually be modeled as:

```text
state_1
→ action_1
→ state_2
→ action_2
→ state_3
...
```

A sequential model can learn relationships across multiple rounds rather than judging each board independently.

---

# Phase 11 — Recommendation Model

Start with simple supervised/ranking baselines before reinforcement learning.

Possible tasks:

```text
current state → roll / level / save
current state → recommended board change
current state → item recommendation
```

Start with:

- rules / statistics baseline
- nearest-neighbor similarity
- XGBoost / simple classifiers
- MLP

Then compare against:

- LSTM
- Transformer

## Evaluation

Recommendations must be measurable. Examples:

- action prediction accuracy
- ranking metrics
- outcome improvement on historical data
- agreement with high-rank decisions
- confidence/calibration

---

# Phase 12 — LLM Explanation Layer

The LLM should explain evidence produced by the recommendation system rather than invent TFT strategy.

Architecture:

```text
video / screenshots
→ CV pipeline
→ structured states/actions
→ recommendation model / retrieval
→ evidence
→ LLM explanation
```

Example structured evidence:

```json
{
  "problem": "rolled too much at stage 3-2",
  "user_action": "spent 28 gold",
  "recommended_action": "save and level",
  "similar_games": 42,
  "high_rank_frequency": 0.71
}
```

Then the LLM converts the evidence into a useful explanation for the player.

---

# Reinforcement Learning — Later

Do **not** prioritize reinforcement learning yet.

RL becomes useful only after the project has:

- reliable state extraction
- reliable action extraction
- meaningful outcome/reward definitions
- enough structured sequential data

Learn it later after the supervised/retrieval baselines are working.

---

# Suggested 6-Month Learning Path

## Month 1 — ML + Math Foundations

- ML fundamentals
- train/validation/test methodology
- metrics
- linear algebra basics
- gradients / chain rule
- gradient descent

Project work: evaluate current TFT classifiers/detectors properly.

## Month 2 — PyTorch From Scratch

- tensors
- autograd
- `nn.Module`
- Dataset / DataLoader
- training loops
- optimizers
- validation

Project work: implement a champion classifier manually in PyTorch.

## Month 3 — CNNs + Image Classification

- convolution
- receptive field
- CNN architectures
- transfer learning
- augmentation
- regularization

Project work: improve champion/star classifiers through controlled experiments.

## Month 4 — Detection + YOLO Internals

- IoU
- NMS
- detection losses
- precision / recall
- mAP
- YOLO architecture

Project work: deeply evaluate and improve board/champion detection.

## Month 5 — Video + Tracking

- FFmpeg
- OpenCV
- frame sampling
- scene/change detection
- ByteTrack
- state transitions

Project work: V2 video → round timeline.

## Month 6 — Sequential Modeling

- embeddings
- similarity search / pgvector
- sequence modeling
- attention
- Transformers

Project work: compare a user game state to similar high-rank states and return evidence-based suggestions.

---

# Learning Rule

For every important concept:

1. Understand the idea.
2. Implement a small version yourself.
3. Apply it to TFT Strength.
4. Measure the result.
5. Write down what changed and why.

Examples:

```text
Learn gradient descent
→ manually update weights once

Learn CNN
→ build one with nn.Conv2d

Learn IoU
→ implement IoU yourself

Learn NMS
→ implement simple NMS

Learn transfer learning
→ compare pretrained vs scratch

Learn class imbalance
→ measure per-class recall
```

The target is to move from:

> I know how to use YOLO/PyTorch.

Toward:

> I understand why the model behaves this way, how to measure the problem, and what experiment I should run next.
