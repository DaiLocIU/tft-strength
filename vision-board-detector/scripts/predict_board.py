import sys
from pathlib import Path
from typing import Optional, TypedDict

import _bootstrap  # noqa: F401
from PIL import Image, ImageDraw
from ultralytics import YOLO  # type: ignore[attr-defined]

from board_detector.model_adapters import BoardDetection, detect_board_box

model = YOLO("models/board-detector.pt")


class BatchCropSummary(TypedDict):
    cropped: list[str]
    failed: list[str]


def detect_board(raw_dir: str = "data/raw", image_name: str = "") -> Optional[BoardDetection]:
    raw_path = Path(raw_dir)
    image_path = raw_path / image_name
    return detect_board_box(image_path, model)


def crop_board(
    image_path: str,
    detection: BoardDetection,
    output_path: str,
) -> None:
    image = Image.open(image_path)

    left = int(detection["x1"])
    top = int(detection["y1"])
    right = int(detection["x2"])
    bottom = int(detection["y2"])

    board_crop = image.crop((left, top, right, bottom))
    crop_path = Path(output_path)
    crop_path.parent.mkdir(parents=True, exist_ok=True)
    board_crop.save(crop_path)


def crop_all_boards(raw_dir: str, output_dir: str) -> BatchCropSummary:
    raw_path = Path(raw_dir)
    output_path = Path(output_dir)

    cropped: list[str] = []
    failed: list[str] = []

    for image_path in sorted(raw_path.glob("*.png")):
        detection = detect_board(raw_dir, image_path.name)

        if detection is None:
            failed.append(image_path.name)
            continue

        crop_file = output_path / image_path.name
        crop_board(str(image_path), detection, str(crop_file))
        cropped.append(image_path.name)

    return {
        "cropped": cropped,
        "failed": failed,
    }


def create_contact_sheet(
    crops_dir: str,
    output_path: str,
    columns: int = 5,
    thumb_width: int = 240,
) -> None:
    crops_path = Path(crops_dir)
    crop_files = sorted(crops_path.glob("*.png"))

    if len(crop_files) == 0:
        print(f"No crop images found in {crops_dir}")
        return

    label_height = 28
    gap = 12
    thumbnails: list[tuple[Path, Image.Image]] = []

    for crop_file in crop_files:
        image = Image.open(crop_file)
        thumb_height = int(image.height * (thumb_width / image.width))
        thumbnail = image.resize((thumb_width, thumb_height))
        thumbnails.append((crop_file, thumbnail))

    max_thumb_height = max(thumbnail.height for _, thumbnail in thumbnails)
    rows = (len(thumbnails) + columns - 1) // columns
    cell_width = thumb_width + gap
    cell_height = max_thumb_height + label_height + gap
    sheet_width = columns * cell_width + gap
    sheet_height = rows * cell_height + gap

    sheet = Image.new("RGB", (sheet_width, sheet_height), "white")
    draw = ImageDraw.Draw(sheet)

    for index, (crop_file, thumbnail) in enumerate(thumbnails):
        row = index // columns
        column = index % columns
        x = gap + column * cell_width
        y = gap + row * cell_height

        sheet.paste(thumbnail, (x, y))
        draw.text((x, y + max_thumb_height + 4), crop_file.name, fill="black")

    review_path = Path(output_path)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(review_path)


if __name__ == "__main__":
    raw_dir = "data/raw"
    output_dir = "outputs/board-crops"
    review_output_path = "outputs/review/board-crops-contact-sheet.png"

    if len(sys.argv) != 2:
        print("Usage: python scripts/predict_board.py <image_name|--all|--contact-sheet>")
        sys.exit(1)

    if sys.argv[1] == "--all":
        summary = crop_all_boards(raw_dir, output_dir)
        print(f"cropped: {len(summary['cropped'])}")
        print(f"failed: {len(summary['failed'])}")
        print(f"failed files: {summary['failed']}")
        sys.exit(0)

    if sys.argv[1] == "--contact-sheet":
        create_contact_sheet(output_dir, review_output_path)
        print(f"saved: {review_output_path}")
        sys.exit(0)

    image_name = sys.argv[1]
    image_path = str(Path(raw_dir) / image_name)
    output_path = str(Path(output_dir) / image_name)

    result = detect_board(raw_dir, image_name)

    if result is None:
        print("No board detected")
    else:
        crop_board(image_path, result, output_path)
        print(f"result: {result}")
        print(f"saved: {output_path}")
