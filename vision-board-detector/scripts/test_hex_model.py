from pathlib import Path
import shutil

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.models import resnet18, ResNet18_Weights

from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score
import time

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

print("Using device:", device)

weights = ResNet18_Weights.DEFAULT

transform = weights.transforms()

base_transform = weights.transforms()

# TRAINING ONLY:
# create slightly different versions of training images
# train_transform = transforms.Compose([
#     transforms.Resize((224, 224)),

#     transforms.RandomHorizontalFlip(p=0.5),

#     transforms.RandomAffine(
#         degrees=3,
#         translate=(0.03, 0.03),
#         scale=(0.95, 1.05),
#     ),

#     transforms.ColorJitter(
#         brightness=0.15,
#         contrast=0.15,
#         saturation=0.10,
#     ),
#     transforms.ToTensor(),

#     transforms.Normalize(
#         mean=[0.485, 0.456, 0.406],
#         std=[0.229, 0.224, 0.225],
#     ),
# ])

# VALIDATION:
# absolutely NO random augmentation
# val_transform = transforms.Compose([
#     transforms.Resize((224, 224)),

#     transforms.ToTensor(),

#     transforms.Normalize(
#         mean=[0.485, 0.456, 0.406],
#         std=[0.229, 0.224, 0.225],
#     ),
# ])


train_transform = base_transform
val_transform = base_transform
dataset = datasets.ImageFolder(
    "data/hex-occupancy/train",
    transform=train_transform,
)

val_dataset = datasets.ImageFolder(
    "data/hex-occupancy/val",
    transform=val_transform,
)

print("Train:", dataset.class_to_idx)
print("Val:", val_dataset.class_to_idx)

assert dataset.class_to_idx == val_dataset.class_to_idx

empty_idx = val_dataset.class_to_idx["empty"]
occupied_idx = val_dataset.class_to_idx["occupied"]


loader = DataLoader(
    dataset,
    batch_size=32,
    shuffle=True,
    num_workers=2,
    persistent_workers=True
)

val_loader = DataLoader(
    val_dataset,
    batch_size=32,
    shuffle=False,
    num_workers=2,
    persistent_workers=True
)
model = resnet18(weights=weights)

model.fc = nn.Linear(model.fc.in_features, 2)

for param in model.parameters():
    param.requires_grad = False

# Fine-tune the last ResNet block
for param in model.layer4.parameters():
    param.requires_grad = True

# Train our new classifier
for param in model.fc.parameters():
    param.requires_grad = True

for name, param in model.named_parameters():
    if not param.requires_grad:
        print("FROZEN:", name)

epochs = 100

optimizer = torch.optim.SGD(
    [
        {
            "params": model.layer4.parameters(),
            "lr": 0.0001,
        },
        {
            "params": model.fc.parameters(),
            "lr": 0.001,
        },
    ],
    momentum=0.9,
    weight_decay=1e-4,
)

scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
    optimizer,
    T_max=epochs,
    eta_min=1e-6,
)

model = model.to(device)


class_weights = torch.tensor(
    [1.0, 2.38],
    device=device
)

loss_fn = nn.CrossEntropyLoss(
    weight=class_weights
)


def main():
    best_accuracy = 0.0
    best_f1 = 0.0
    best_epoch = -1
    patience = 100
    epochs_without_improvement = 0
    checkpoint_path = "best_resnet18_sgd_augmented.pth"

    for epoch in range(epochs):
        epoch_start = time.time()

        # ==================
        # TRAIN
        # ==================
        train_start = time.time()
        model.train()

        total_loss = 0

        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            loss = loss_fn(outputs, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        average_loss = total_loss / len(loader)
        train_time = time.time() - train_start
        # --------------------
        # VALIDATION
        # --------------------
        val_start = time.time()
        model.eval()
        all_predictions = []
        all_labels = []
        all_occupied_probs = []

        correct = 0
        total = 0

        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device)
                outputs = model(images)
                probabilities = torch.softmax(outputs, dim=1)
                predictions = probabilities.argmax(dim=1)
                occupied_probs = probabilities[:, occupied_idx]

                correct += (predictions == labels).sum().item()
                total += labels.size(0)

                all_predictions.extend(predictions.cpu().tolist())
                all_labels.extend(labels.cpu().tolist())
                all_occupied_probs.extend(occupied_probs.cpu().tolist())

        val_accuracy = correct / total
        val_time = time.time() - val_start
        epoch_time = time.time() - epoch_start

        print(f"epoch: {epoch}")
        print(f"Train time: {train_time:.2f}s")
        print(f"Val time:   {val_time:.2f}s")
        print(f"Epoch time: {epoch_time:.2f}s")
        print(f"Validation accuracy: {val_accuracy:.2%}")

        tn, fp, fn, tp = confusion_matrix(
            all_labels,
            all_predictions,
            labels=[empty_idx, occupied_idx],
        ).ravel()

        precision = precision_score(
            all_labels,
            all_predictions,
            pos_label=occupied_idx,
            zero_division=0,
        )

        recall = recall_score(
            all_labels,
            all_predictions,
            pos_label=occupied_idx,
            zero_division=0,
        )

        f1 = f1_score(
            all_labels,
            all_predictions,
            pos_label=occupied_idx,
            zero_division=0,
        )

        print("TP:", tp)
        print("TN:", tn)
        print("FP:", fp)
        print("FN:", fn)

        print(f"Precision: {precision:.2%}")
        print(f"Recall: {recall:.2%}")
        print(f"F1: {f1:.2%}")

        if f1 > best_f1:
            best_accuracy = val_accuracy
            best_f1 = f1
            best_epoch = epoch

            epochs_without_improvement = 0

            torch.save(
                model.state_dict(),
                checkpoint_path
            )

            print(
                f"✅ Saved best model at: {epoch} "
                f"(f1: {f1:.2%})"
            )

        else:
            epochs_without_improvement += 1

        current_lr = optimizer.param_groups[0]["lr"]
        print(f"Learning rate: {current_lr:.8f}")
        scheduler.step()

        if epochs_without_improvement >= patience:
            print(
                f"Early stopping: no improvement for "
                f"{patience} epochs"
            )
            break

    # ==========================================
    # ERROR ANALYSIS USING BEST SAVED MODEL
    # ==========================================
    print(f"\nBest epoch: {best_epoch}")
    print(f"Best accuracy: {best_accuracy:.2%}")
    print(f"F1 at best accuracy: {best_f1:.2%}")
    print("\nLoading best model for error analysis...")

    model.load_state_dict(
        torch.load(
            checkpoint_path,
            map_location=device
        )
    )

    model.eval()

    all_predictions = []
    all_labels = []
    all_occupied_probs = []

    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            probabilities = torch.softmax(outputs, dim=1)
            predictions = probabilities.argmax(dim=1)

            occupied_probs = probabilities[:, occupied_idx]

            all_predictions.extend(
                predictions.cpu().tolist()
            )

            all_labels.extend(
                labels.cpu().tolist()
            )

            all_occupied_probs.extend(
                occupied_probs.cpu().tolist()
            )


    error_dir = Path("data/hex-occupancy/preview_errors_resnet18")

    fn_dir = error_dir / "fn"
    fp_dir = error_dir / "fp"

    # Remove old previews so they don't mix with this run
    if error_dir.exists():
        shutil.rmtree(error_dir)

    fn_dir.mkdir(parents=True)
    fp_dir.mkdir(parents=True)

    fn_count = 0
    fp_count = 0

    for index, ((image_path, label), prediction, occupied_prob) in enumerate(
        zip(val_dataset.samples, all_predictions, all_occupied_probs)
    ):
        image_path = Path(image_path)

        # False Negative
        # actual occupied, predicted empty
        if label == occupied_idx and prediction == empty_idx:
            assert occupied_prob <= 0.5
            destination = fn_dir / (
                f"{index}_occupied_{occupied_prob:.3f}_{image_path.name}"
            )

            shutil.copy2(image_path, destination)

            fn_count += 1

        # False Positive
        # actual empty, predicted occupied
        elif label == empty_idx and prediction == occupied_idx:
            assert occupied_prob > 0.5
            destination = fp_dir / (
                f"{index}_occupied_{occupied_prob:.3f}_{image_path.name}"
            )
            shutil.copy2(
                image_path,
                destination
            )

            fp_count += 1

    print(f"Saved FN images: {fn_count}")
    print(f"Saved FP images: {fp_count}")
    print(f"Preview folder: {error_dir}")


if __name__ == "__main__":
    main()
