import sys
from pathlib import Path

import _bootstrap  # noqa: F401
from PIL import Image, ImageDraw

from board_detector.board_geometry import (
    HexCell,
    HexTuning,
    create_board_hex_cells,
    create_hex_polygon,
)

CONTACT_SHEET_FLAGS = {"--contact-sheet", "--bottom-row-contact-sheet"}


def draw_hex_cells_on_image(image: Image.Image, hexes: list[HexCell]) -> None:
    draw = ImageDraw.Draw(image)

    for hex_cell in hexes:
        center_x = hex_cell["center_x"]
        center_y = hex_cell["center_y"]
        label = f"{hex_cell['row']},{hex_cell['column']}"
        polygon = create_hex_polygon(hex_cell)

        draw.polygon(polygon, outline="red", width=4)
        dot_radius = 8
        draw.ellipse(
            (
                center_x - dot_radius,
                center_y - dot_radius,
                center_x + dot_radius,
                center_y + dot_radius,
            ),
            fill="red",
        )
        draw.text((center_x + 10, center_y - 8), label, fill="white")


def draw_hex_center(
    image_path: str,
    hex_cell: HexCell,
    output_path: str,
) -> None:
    image = Image.open(image_path).convert("RGB")
    draw_hex_cells_on_image(image, [hex_cell])

    review_path = Path(output_path)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(review_path)


def draw_hex_cells(
    image_path: str,
    hexes: list[HexCell],
    output_path: str,
) -> None:
    image = Image.open(image_path).convert("RGB")
    draw_hex_cells_on_image(image, hexes)

    review_path = Path(output_path)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(review_path)


def create_board_hex_contact_sheet(
    crops_dir: str,
    output_path: str,
    tuning: HexTuning,
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
        hexes = create_board_hex_cells(str(crop_file), tuning)
        image = Image.open(crop_file).convert("RGB")
        draw_hex_cells_on_image(image, hexes)

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


def read_tuning_args(args: list[str]) -> HexTuning:
    tuning: HexTuning = {
        "width_percent": 13.5,
        "height_percent": 90.0,
        "radius_percent": 5.4,
        "gap_percent": 3.7,
        "image_name": "image_1.png",
    }

    for arg in args:
        if "=" not in arg:
            print(f"Unknown argument: {arg}")
            print(
                "Usage: python scripts/detect_hexes.py "
                "[--bottom-row-contact-sheet] "
                "width=13.4 height=90 radius=6.1 gap=3.4 image=image_1.png"
            )
            sys.exit(1)

        key, value = arg.split("=", 1)

        if key == "width":
            tuning["width_percent"] = float(value)
        elif key == "height":
            tuning["height_percent"] = float(value)
        elif key == "radius":
            tuning["radius_percent"] = float(value)
        elif key == "gap":
            tuning["gap_percent"] = float(value)
        elif key == "image":
            tuning["image_name"] = value
        else:
            print(f"Unknown argument: {arg}")
            print(
                "Usage: python scripts/detect_hexes.py "
                "[--bottom-row-contact-sheet] "
                "width=13.4 height=90 radius=6.1 gap=3.4 image=image_1.png"
            )
            sys.exit(1)

    return tuning


if __name__ == "__main__":
    contact_sheet_requested = any(arg in CONTACT_SHEET_FLAGS for arg in sys.argv[1:])
    tuning_args = [arg for arg in sys.argv[1:] if arg not in CONTACT_SHEET_FLAGS]
    tuning = read_tuning_args(tuning_args)
    crops_dir = "outputs/board-crops"
    overlays_dir = "outputs/hex-overlays"
    review_dir = "outputs/review"
    image_name = tuning["image_name"]
    crop_path = str(Path(crops_dir) / image_name)
    overlay_path = str(Path(overlays_dir) / "four-rows.png")
    contact_sheet_path = str(Path(review_dir) / "board-hex-four-rows-contact-sheet.png")

    if contact_sheet_requested:
        create_board_hex_contact_sheet(
            crops_dir,
            contact_sheet_path,
            tuning,
        )
        print(f"saved: {contact_sheet_path}")
        sys.exit(0)

    all_rows = create_board_hex_cells(crop_path, tuning)

    draw_hex_cells(
        crop_path,
        all_rows,
        overlay_path,
    )
    print(all_rows)
    print(f"hexes: {len(all_rows)}")
