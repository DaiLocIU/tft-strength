import argparse
import random
import shutil
from pathlib import Path


DATASET_DIR = Path("data/champion-identity")
LABELED_DIR = DATASET_DIR / "labeled"
VAL_RATIO = 0.2
RANDOM_SEED = 7
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def normalize_class_names(class_names: list[str]) -> list[str]:
    return sorted({class_name.strip().lower() for class_name in class_names if class_name.strip()})


def init_labeled_dirs(class_names: list[str]) -> None:
    for class_name in normalize_class_names(class_names):
        (LABELED_DIR / class_name).mkdir(parents=True, exist_ok=True)
        print(f"created: {LABELED_DIR / class_name}")


def get_labeled_class_dirs() -> list[Path]:
    if not LABELED_DIR.exists():
        raise FileNotFoundError(
            f"Labeled directory not found: {LABELED_DIR}. "
            "Run --init first, then put champion crops into class folders."
        )

    return sorted([path for path in LABELED_DIR.iterdir() if path.is_dir()])


def get_image_files(class_dir: Path) -> list[Path]:
    return sorted(
        [
            path
            for path in class_dir.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        ]
    )


def clear_existing_split() -> None:
    for split_name in ["train", "val"]:
        split_dir = DATASET_DIR / split_name

        if split_dir.exists():
            shutil.rmtree(split_dir)


def choose_val_files(image_files: list[Path]) -> set[Path]:
    if len(image_files) < 2:
        return set()

    shuffled_files = image_files[:]
    random.Random(RANDOM_SEED).shuffle(shuffled_files)
    val_count = max(1, round(len(shuffled_files) * VAL_RATIO))
    return set(shuffled_files[:val_count])


def copy_file_to_split(image_file: Path, split_name: str) -> None:
    class_name = image_file.parent.name
    output_dir = DATASET_DIR / split_name / class_name
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(image_file, output_dir / image_file.name)


def split_champion_identity_dataset() -> None:
    class_dirs = get_labeled_class_dirs()

    if len(class_dirs) == 0:
        raise ValueError(f"No champion class folders found in {LABELED_DIR}")

    clear_existing_split()

    for class_dir in class_dirs:
        image_files = get_image_files(class_dir)
        val_files = choose_val_files(image_files)

        for image_file in image_files:
            if len(image_files) == 1:
                copy_file_to_split(image_file, "train")
                copy_file_to_split(image_file, "val")
                continue

            split_name = "val" if image_file in val_files else "train"
            copy_file_to_split(image_file, split_name)

        train_count = 1 if len(image_files) == 1 else len(image_files) - len(val_files)
        val_count = 1 if len(image_files) == 1 else len(val_files)
        print(f"{class_dir.name}: train={train_count} val={val_count}")

    print(f"saved: {DATASET_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--classes", nargs="*", default=["kayle", "nunu", "unknown"])
    args = parser.parse_args()

    if args.init:
        init_labeled_dirs(args.classes)
        return

    split_champion_identity_dataset()


if __name__ == "__main__":
    main()
