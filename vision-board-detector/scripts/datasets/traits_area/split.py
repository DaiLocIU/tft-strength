"""Split paired traits-area YOLO images and labels into train and val sets."""

import argparse
import random
import shutil
from pathlib import Path

IMAGE_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg"}
TRAIN_RATIO = 0.8
RANDOM_SEED = 7


def image_files(images_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in images_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def validate_pairs(images: list[Path], labels_dir: Path) -> None:
    missing_labels = [
        image.name for image in images if not (labels_dir / f"{image.stem}.txt").is_file()
    ]
    if missing_labels:
        raise ValueError("Images without matching YOLO labels: " + ", ".join(missing_labels))


def select_validation_images(images: list[Path], seed: int) -> set[Path]:
    if len(images) < 2:
        raise ValueError("At least two labeled images are required for a train/val split")

    shuffled = images[:]
    random.Random(seed).shuffle(shuffled)
    validation_count = max(1, round(len(shuffled) * (1 - TRAIN_RATIO)))
    return set(shuffled[:validation_count])


def copy_pair(image: Path, labels_dir: Path, dataset_dir: Path, split_name: str) -> None:
    image_destination = dataset_dir / "images" / split_name / image.name
    label_destination = dataset_dir / "labels" / split_name / f"{image.stem}.txt"
    image_destination.parent.mkdir(parents=True, exist_ok=True)
    label_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(image, image_destination)
    shutil.copy2(labels_dir / f"{image.stem}.txt", label_destination)


def clear_existing_splits(dataset_dir: Path) -> None:
    for data_type in ("images", "labels"):
        for split_name in ("train", "val"):
            split_dir = dataset_dir / data_type / split_name
            if split_dir.exists():
                shutil.rmtree(split_dir)


def split_traits_area_dataset(
    images_dir: Path,
    labels_dir: Path,
    dataset_dir: Path,
    seed: int = RANDOM_SEED,
    replace: bool = False,
) -> tuple[int, int]:
    if not images_dir.is_dir():
        raise FileNotFoundError(f"Image directory not found: {images_dir}")
    if not labels_dir.is_dir():
        raise FileNotFoundError(f"Label directory not found: {labels_dir}")

    images = image_files(images_dir)
    if not images:
        raise ValueError(f"No images found in: {images_dir}")
    validate_pairs(images, labels_dir)

    if replace:
        clear_existing_splits(dataset_dir)

    validation_images = select_validation_images(images, seed)
    for image in images:
        split_name = "val" if image in validation_images else "train"
        copy_pair(image, labels_dir, dataset_dir, split_name)

    return len(images) - len(validation_images), len(validation_images)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=Path("data/traits-area/source/images"),
        help="Directory containing the unsplit traits-area screenshots",
    )
    parser.add_argument(
        "--labels-dir",
        type=Path,
        default=Path("data/traits-area/source/labels"),
        help="Directory containing one matching YOLO .txt file per screenshot",
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=Path("data/traits-area"),
        help="Destination for images/{train,val} and labels/{train,val}",
    )
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing train and val directories before copying the new split",
    )
    args = parser.parse_args()

    train_count, val_count = split_traits_area_dataset(
        args.images_dir,
        args.labels_dir,
        args.dataset_dir,
        seed=args.seed,
        replace=args.replace,
    )
    print(f"train images: {train_count}")
    print(f"val images: {val_count}")
    print(f"saved: {args.dataset_dir}")


if __name__ == "__main__":
    main()
