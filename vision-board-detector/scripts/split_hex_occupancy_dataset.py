import shutil
from pathlib import Path
from typing import TypedDict


class SplitCounts(TypedDict):
    train_occupied: int
    train_empty: int
    val_occupied: int
    val_empty: int


LABELED_DIR = Path("data/hex-occupancy/labeled")
DATASET_DIR = Path("data/hex-occupancy")
CLASSES = ["occupied", "empty"]
VAL_RATIO = 0.2


def get_source_image_key(patch_file: Path) -> str:
    return patch_file.stem.rsplit("_r", 1)[0]


def collect_patch_files() -> dict[str, list[Path]]:
    patch_files_by_source: dict[str, list[Path]] = {}

    for class_name in CLASSES:
        class_dir = LABELED_DIR / class_name

        for patch_file in sorted(class_dir.glob("*.png")):
            source_key = get_source_image_key(patch_file)

            if source_key not in patch_files_by_source:
                patch_files_by_source[source_key] = []

            patch_files_by_source[source_key].append(patch_file)

    return patch_files_by_source


def choose_val_source_keys(source_keys: list[str]) -> set[str]:
    val_count = int(round(len(source_keys) * VAL_RATIO))
    val_count = max(val_count, 1)
    return set(source_keys[-val_count:])


def get_split_name(source_key: str, val_source_keys: set[str]) -> str:
    if source_key in val_source_keys:
        return "val"

    return "train"


def get_class_name(patch_file: Path) -> str:
    return patch_file.parent.name


def copy_patch_to_split(patch_file: Path, split_name: str) -> None:
    class_name = get_class_name(patch_file)
    output_dir = DATASET_DIR / split_name / class_name
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(patch_file, output_dir / patch_file.name)


def clear_existing_split() -> None:
    for split_name in ["train", "val"]:
        split_dir = DATASET_DIR / split_name

        if split_dir.exists():
            shutil.rmtree(split_dir)


def count_split_files() -> SplitCounts:
    return {
        "train_occupied": len(list((DATASET_DIR / "train" / "occupied").glob("*.png"))),
        "train_empty": len(list((DATASET_DIR / "train" / "empty").glob("*.png"))),
        "val_occupied": len(list((DATASET_DIR / "val" / "occupied").glob("*.png"))),
        "val_empty": len(list((DATASET_DIR / "val" / "empty").glob("*.png"))),
    }


def split_hex_occupancy_dataset() -> SplitCounts:
    patch_files_by_source = collect_patch_files()
    source_keys = sorted(patch_files_by_source.keys())

    if len(source_keys) == 0:
        raise ValueError(f"No labeled patch files found in {LABELED_DIR}")

    clear_existing_split()

    val_source_keys = choose_val_source_keys(source_keys)

    for source_key in source_keys:
        split_name = get_split_name(source_key, val_source_keys)

        for patch_file in patch_files_by_source[source_key]:
            copy_patch_to_split(patch_file, split_name)

    return count_split_files()


def print_counts(counts: SplitCounts) -> None:
    print(f"train/occupied: {counts['train_occupied']}")
    print(f"train/empty:    {counts['train_empty']}")
    print(f"val/occupied:   {counts['val_occupied']}")
    print(f"val/empty:      {counts['val_empty']}")


def main() -> None:
    counts = split_hex_occupancy_dataset()
    print_counts(counts)


if __name__ == "__main__":
    main()
