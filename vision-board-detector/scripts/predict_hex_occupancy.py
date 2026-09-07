import sys
from pathlib import Path
from typing import Optional, TypedDict, Union

import _bootstrap  # noqa: F401
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO  # type: ignore[attr-defined]

from board_detector.board_geometry import (
    DEFAULT_TUNING,
    HexCell,
    create_board_hex_cells,
    create_hex_polygon,
    make_tuning_for_image,
)
from board_detector.model_adapters import HexOccupancyPrediction
from board_detector.model_adapters import (
    classify_hex_occupancy as classify_hex_occupancy_with_model,
)


class BatchPredictionSummary(TypedDict):
    images: int
    total_occupied: int
    output_files: list[str]


CROPS_DIR = Path("outputs/board-crops")
OUTPUT_DIR = Path("outputs/hex-occupancy")
REVIEW_DIR = Path("outputs/review/hex-occupancy-predictions")
MODEL_PATH = Path("models/hex-occupancy-classifier.pt")
OCCUPIED_CONFIDENCE_THRESHOLD = 0.5
CONFIDENCE_FONT_SIZE = 28


def predict_one_hex(
    model: YOLO,
    board_image: Image.Image,
    hex_cell: HexCell,
) -> HexOccupancyPrediction:
    return classify_hex_occupancy_with_model(
        model,
        board_image,
        hex_cell,
        96,
        OCCUPIED_CONFIDENCE_THRESHOLD,
    )


def predict_board_hex_occupancy(
    board_crop_path: Path,
    model_path: Path,
    model: Optional[YOLO] = None,
) -> list[HexOccupancyPrediction]:
    image_name = board_crop_path.name
    board_image = Image.open(board_crop_path).convert("RGB")
    hexes = sorted(
        create_board_hex_cells(str(board_crop_path), make_tuning_for_image(image_name)),
        key=lambda hex_cell: (hex_cell["row"], hex_cell["column"]),
    )
    classifier_model = model

    if classifier_model is None:
        classifier_model = YOLO(model_path)

    return [predict_one_hex(classifier_model, board_image, hex_cell) for hex_cell in hexes]


def load_confidence_font() -> Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]:
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]

    for font_path in font_paths:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, CONFIDENCE_FONT_SIZE)

    return ImageFont.load_default()


def draw_text_with_background(
    draw: ImageDraw.ImageDraw,
    position: tuple[float, float],
    text: str,
    font: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont],
) -> None:
    x, y = position
    padding = 5
    bbox = draw.textbbox((x, y), text, font=font)
    background_box = (
        bbox[0] - padding,
        bbox[1] - padding,
        bbox[2] + padding,
        bbox[3] + padding,
    )
    draw.rectangle(background_box, fill=(0, 0, 0, 180))
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)


def draw_prediction_overlay(
    board_crop_path: Path,
    predictions: list[HexOccupancyPrediction],
    output_path: Path,
) -> None:
    image = Image.open(board_crop_path).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    confidence_font = load_confidence_font()

    hexes = sorted(
        create_board_hex_cells(str(board_crop_path), make_tuning_for_image(board_crop_path.name)),
        key=lambda hex_cell: (hex_cell["row"], hex_cell["column"]),
    )

    predictions_by_cell = {
        (prediction["row"], prediction["column"]): prediction for prediction in predictions
    }

    for hex_cell in hexes:
        prediction = predictions_by_cell[(hex_cell["row"], hex_cell["column"])]
        polygon = create_hex_polygon(hex_cell)
        label = f"{hex_cell['row']},{hex_cell['column']} {prediction['confidence']:.2f}"

        if prediction["occupied"]:
            draw.polygon(polygon, fill=(220, 38, 38, 95), outline=(220, 38, 38, 255))
            draw_text_with_background(
                draw,
                (hex_cell["center_x"] - hex_cell["radius"] * 0.45, hex_cell["center_y"] - 12),
                label,
                confidence_font,
            )
        else:
            draw.line(polygon + [polygon[0]], fill=(20, 184, 166, 150), width=3)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(image, overlay).convert("RGB").save(output_path)


def print_occupied_predictions(predictions: list[HexOccupancyPrediction]) -> None:
    occupied_predictions = [prediction for prediction in predictions if prediction["occupied"]]

    if len(occupied_predictions) == 0:
        print("No occupied hexes predicted.")
        return

    for prediction in occupied_predictions:
        print(
            "occupied: "
            f"row={prediction['row']} "
            f"column={prediction['column']} "
            f"confidence={prediction['confidence']:.2f}"
        )


def count_occupied_predictions(predictions: list[HexOccupancyPrediction]) -> int:
    return len([prediction for prediction in predictions if prediction["occupied"]])


def predict_all_board_crops() -> BatchPredictionSummary:
    board_crop_paths = sorted(CROPS_DIR.glob("*.png"))
    model = YOLO(MODEL_PATH)
    output_files: list[str] = []
    total_occupied = 0

    for index, board_crop_path in enumerate(board_crop_paths, start=1):
        predictions = predict_board_hex_occupancy(board_crop_path, MODEL_PATH, model)
        occupied_count = count_occupied_predictions(predictions)
        total_occupied += occupied_count

        output_path = OUTPUT_DIR / f"{board_crop_path.stem}-predicted.png"
        draw_prediction_overlay(board_crop_path, predictions, output_path)
        output_files.append(str(output_path))

        print(
            f"{index}/{len(board_crop_paths)} "
            f"{board_crop_path.name}: {occupied_count} occupied"
        )

    return {
        "images": len(board_crop_paths),
        "total_occupied": total_occupied,
        "output_files": output_files,
    }


def create_prediction_contact_sheet_page(
    image_files: list[Path],
    output_path: Path,
    title: str,
    columns: int = 4,
    thumb_width: int = 300,
) -> None:
    label_height = 24
    title_height = 42
    gap = 10
    thumbnails: list[tuple[Path, Image.Image]] = []

    for image_file in image_files:
        image = Image.open(image_file).convert("RGB")
        thumb_height = int(image.height * (thumb_width / image.width))
        thumbnail = image.resize((thumb_width, thumb_height))
        thumbnails.append((image_file, thumbnail))

    max_thumb_height = max(thumbnail.height for _, thumbnail in thumbnails)
    rows = (len(thumbnails) + columns - 1) // columns
    cell_width = thumb_width + gap
    cell_height = max_thumb_height + label_height + gap
    sheet_width = columns * cell_width + gap
    sheet_height = title_height + rows * cell_height + gap

    sheet = Image.new("RGB", (sheet_width, sheet_height), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((gap, 12), title, fill="black")

    for index, (image_file, thumbnail) in enumerate(thumbnails):
        row = index // columns
        column = index % columns
        x = gap + column * cell_width
        y = title_height + row * cell_height

        sheet.paste(thumbnail, (x, y))
        draw.text((x, y + max_thumb_height + 4), image_file.name, fill="black")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def create_prediction_contact_sheets(images_per_page: int = 40) -> list[str]:
    image_files = sorted(OUTPUT_DIR.glob("*-predicted.png"))
    output_files: list[str] = []

    if len(image_files) == 0:
        print(f"No prediction images found in {OUTPUT_DIR}")
        return output_files

    page_count = (len(image_files) + images_per_page - 1) // images_per_page

    for page_index in range(page_count):
        start = page_index * images_per_page
        end = start + images_per_page
        page_files = image_files[start:end]
        output_path = REVIEW_DIR / f"predictions-page-{page_index + 1:03}.png"
        title = (
            f"hex occupancy predictions "
            f"page {page_index + 1}/{page_count} "
            f"({len(page_files)} boards)"
        )
        create_prediction_contact_sheet_page(page_files, output_path, title)
        output_files.append(str(output_path))

    return output_files


def ensure_model_exists() -> None:
    if not MODEL_PATH.exists():
        print(f"Classifier model not found: {MODEL_PATH}")
        sys.exit(1)


def main() -> None:
    image_name = DEFAULT_TUNING["image_name"]

    ensure_model_exists()

    if len(sys.argv) == 2 and sys.argv[1] == "--all":
        summary = predict_all_board_crops()
        contact_sheet_files = create_prediction_contact_sheets()
        print(f"images: {summary['images']}")
        print(f"total occupied predictions: {summary['total_occupied']}")
        print(f"contact sheets: {len(contact_sheet_files)}")
        sys.exit(0)

    if len(sys.argv) == 2 and sys.argv[1] == "--contact-sheet":
        contact_sheet_files = create_prediction_contact_sheets()

        for contact_sheet_file in contact_sheet_files:
            print(f"saved: {contact_sheet_file}")

        sys.exit(0)

    if len(sys.argv) == 2:
        image_name = sys.argv[1]
    elif len(sys.argv) > 2:
        print("Usage: python scripts/predict_hex_occupancy.py [image_name|--all|--contact-sheet]")
        sys.exit(1)

    board_crop_path = CROPS_DIR / image_name

    if not board_crop_path.exists():
        print(f"Board crop not found: {board_crop_path}")
        sys.exit(1)

    output_path = OUTPUT_DIR / f"{board_crop_path.stem}-predicted.png"
    predictions = predict_board_hex_occupancy(board_crop_path, MODEL_PATH)
    print_occupied_predictions(predictions)
    draw_prediction_overlay(board_crop_path, predictions, output_path)
    print(f"saved: {output_path}")


if __name__ == "__main__":
    main()
