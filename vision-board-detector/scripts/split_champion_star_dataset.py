import argparse
import random
import shutil
from pathlib import Path

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


def image_paths(class_dir: Path) -> list[Path]:
    return sorted(path for path in class_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)


def split_class_images(
    class_dir: Path,
    output_dir: Path,
    train_ratio: float,
    rng: random.Random,
) -> tuple[int, int]:
    images = image_paths(class_dir)
    rng.shuffle(images)

    split_index = max(1, int(len(images) * train_ratio)) if len(images) > 0 else 0
    parts = [
        ("train", images[:split_index]),
        ("val", images[split_index:]),
    ]

    for part, part_images in parts:
        part_dir = output_dir / part / class_dir.name
        part_dir.mkdir(parents=True, exist_ok=True)
        for image in part_images:
            shutil.copy2(image, part_dir / image.name)

    return len(parts[0][1]), len(parts[1][1])


def split_dataset(
    labeled_dir: Path,
    output_dir: Path,
    train_ratio: float,
    seed: int,
    clear_existing: bool,
) -> None:
    if clear_existing and output_dir.exists():
        shutil.rmtree(output_dir)

    rng = random.Random(seed)
    class_dirs = sorted(path for path in labeled_dir.iterdir() if path.is_dir())
    if len(class_dirs) == 0:
        raise FileNotFoundError(f"No class folders found in: {labeled_dir}")

    total_train = 0
    total_val = 0
    for class_dir in class_dirs:
        train_count, val_count = split_class_images(class_dir, output_dir, train_ratio, rng)
        total_train += train_count
        total_val += val_count
        print(f"{class_dir.name}: train={train_count} val={val_count}")

    print(f"train images: {total_train}")
    print(f"val images: {total_val}")
    print(f"saved: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labeled-dir", type=Path, default=Path("data/champion-star/labeled"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/champion-star-dataset"))
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--keep-existing", action="store_true")
    args = parser.parse_args()

    split_dataset(
        args.labeled_dir,
        args.output_dir,
        args.train_ratio,
        args.seed,
        clear_existing=not args.keep_existing,
    )


if __name__ == "__main__":
    main()
