import argparse
import random
import shutil
import zipfile
from pathlib import Path


EXPORT_ZIP = Path("exports/label-studio/champion.zip")
DATASET_DIR = Path("data/champion-detector")
CLASS_NAME = "champion"
VAL_RATIO = 0.2
RANDOM_SEED = 7


def clean_dataset_dir() -> None:
    if DATASET_DIR.exists():
        shutil.rmtree(DATASET_DIR)

    for split_name in ["train", "val"]:
        (DATASET_DIR / "images" / split_name).mkdir(parents=True, exist_ok=True)
        (DATASET_DIR / "labels" / split_name).mkdir(parents=True, exist_ok=True)


def extract_export(export_zip: Path, extract_dir: Path) -> None:
    if not export_zip.exists():
        raise FileNotFoundError(f"Export zip not found: {export_zip}")

    if extract_dir.exists():
        shutil.rmtree(extract_dir)

    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(export_zip) as archive:
        archive.extractall(extract_dir)


def get_image_files(extract_dir: Path) -> list[Path]:
    image_dir = extract_dir / "images"
    image_files = sorted(
        [
            *image_dir.glob("*.png"),
            *image_dir.glob("*.jpg"),
            *image_dir.glob("*.jpeg"),
        ]
    )

    if len(image_files) == 0:
        raise ValueError(f"No images found in {image_dir}")

    return image_files


def choose_val_images(image_files: list[Path]) -> set[str]:
    shuffled_files = image_files[:]
    random.Random(RANDOM_SEED).shuffle(shuffled_files)
    val_count = max(1, round(len(shuffled_files) * VAL_RATIO))
    return {image_file.name for image_file in shuffled_files[:val_count]}


def copy_image_and_label(image_file: Path, extract_dir: Path, split_name: str) -> None:
    label_file = extract_dir / "labels" / f"{image_file.stem}.txt"
    output_image = DATASET_DIR / "images" / split_name / image_file.name
    output_label = DATASET_DIR / "labels" / split_name / f"{image_file.stem}.txt"

    shutil.copy2(image_file, output_image)

    if label_file.exists():
        shutil.copy2(label_file, output_label)
    else:
        output_label.write_text("", encoding="utf-8")


def write_data_yaml() -> None:
    data_yaml = "\n".join(
        [
            f"path: {DATASET_DIR}",
            "train: images/train",
            "val: images/val",
            "names:",
            f"  0: {CLASS_NAME}",
            "",
        ]
    )
    (DATASET_DIR / "data.yaml").write_text(data_yaml, encoding="utf-8")


def prepare_dataset(export_zip: Path) -> None:
    extract_dir = DATASET_DIR / "_label_studio_export"
    clean_dataset_dir()
    extract_export(export_zip, extract_dir)

    image_files = get_image_files(extract_dir)
    val_image_names = choose_val_images(image_files)

    for image_file in image_files:
        split_name = "val" if image_file.name in val_image_names else "train"
        copy_image_and_label(image_file, extract_dir, split_name)

    write_data_yaml()
    shutil.rmtree(extract_dir)

    train_count = len(list((DATASET_DIR / "images" / "train").glob("*")))
    val_count = len(list((DATASET_DIR / "images" / "val").glob("*")))
    print(f"train images: {train_count}")
    print(f"val images:   {val_count}")
    print(f"data yaml:    {DATASET_DIR / 'data.yaml'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", type=Path, default=EXPORT_ZIP)
    args = parser.parse_args()
    prepare_dataset(args.export)


if __name__ == "__main__":
    main()
