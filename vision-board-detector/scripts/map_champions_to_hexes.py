import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
from PIL import Image, ImageDraw
from ultralytics import YOLO  # type: ignore[attr-defined]

from board_detector.board_geometry import (
    HexCell,
    create_board_hex_cells,
    create_hex_polygon,
    make_tuning_for_image,
)
from board_detector.champion_hex_evidence import (
    DEFAULT_FOOT_OFFSET_RATIO,
    ChampionHexAssignment,
    assign_champions_to_hexes,
    predict_champion_boxes,
)

MODEL_PATH = "models/champion-detector.pt"
CROPS_DIR = "outputs/board-crops"
OUTPUT_DIR = "outputs/champion-hex-map"
DEFAULT_CONFIDENCE = 0.5


def draw_all_hexes(draw: ImageDraw.ImageDraw, hexes: list[HexCell]) -> None:
    for hex_cell in hexes:
        draw.polygon(create_hex_polygon(hex_cell), outline="gray", width=2)


def draw_assignment(draw: ImageDraw.ImageDraw, assignment: ChampionHexAssignment) -> None:
    box = assignment["box"]
    hex_cell = assignment["hex"]
    point_x = assignment["point_x"]
    point_y = assignment["point_y"]
    label = f"{hex_cell['row']},{hex_cell['column']} {box['confidence']:.2f}"

    draw.rectangle(
        (box["x1"], box["y1"], box["x2"], box["y2"]),
        outline="lime",
        width=4,
    )
    draw.ellipse(
        (point_x - 7, point_y - 7, point_x + 7, point_y + 7),
        fill="yellow",
        outline="black",
        width=2,
    )
    draw.polygon(create_hex_polygon(hex_cell), outline="red", width=5)
    draw.text((point_x + 8, point_y - 18), label, fill="white")


def draw_review_image(
    image_path: Path,
    hexes: list[HexCell],
    assignments: list[ChampionHexAssignment],
    output_path: Path,
) -> None:
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    draw_all_hexes(draw, hexes)

    for assignment in assignments:
        draw_assignment(draw, assignment)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def map_champions_to_hexes(
    image_name: str,
    model: YOLO,
    confidence: float,
    foot_offset_ratio: float,
    quiet: bool = False,
) -> list[ChampionHexAssignment]:
    image_path = Path(CROPS_DIR) / image_name

    if not image_path.exists():
        raise FileNotFoundError(f"Board crop not found: {image_path}")

    hexes = create_board_hex_cells(str(image_path), make_tuning_for_image(image_name))
    champion_boxes = predict_champion_boxes(image_path, model, confidence)
    image_height = Image.open(image_path).height
    assignments = assign_champions_to_hexes(
        champion_boxes,
        hexes,
        image_height,
        foot_offset_ratio,
    )
    output_path = Path(OUTPUT_DIR) / f"{Path(image_name).stem}-champion-hex-map.png"

    draw_review_image(image_path, hexes, assignments, output_path)

    if quiet:
        return assignments

    print(f"champions: {len(assignments)}")
    for assignment in assignments:
        hex_cell = assignment["hex"]
        box = assignment["box"]
        print(
            f"hex: row={hex_cell['row']} column={hex_cell['column']} "
            f"confidence={box['confidence']:.2f}"
        )
    print(f"saved: {output_path}")

    return assignments


def map_all_board_crops(confidence: float, foot_offset_ratio: float) -> None:
    crop_files = sorted(Path(CROPS_DIR).glob("*.png"))

    if len(crop_files) == 0:
        raise FileNotFoundError(f"No board crops found in: {CROPS_DIR}")

    model = YOLO(MODEL_PATH)
    total_champions = 0

    for crop_file in crop_files:
        assignments = map_champions_to_hexes(
            crop_file.name,
            model,
            confidence,
            foot_offset_ratio,
            quiet=True,
        )
        total_champions += len(assignments)
        print(f"{crop_file.name}: {len(assignments)} champions")

    print(f"images: {len(crop_files)}")
    print(f"champions: {total_champions}")
    print(f"saved: {OUTPUT_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image_name", nargs="?", default="image_1.png")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--conf", type=float, default=DEFAULT_CONFIDENCE)
    parser.add_argument("--foot-offset", type=float, default=DEFAULT_FOOT_OFFSET_RATIO)
    args = parser.parse_args()

    if args.all:
        map_all_board_crops(args.conf, args.foot_offset)
        return

    model = YOLO(MODEL_PATH)
    map_champions_to_hexes(args.image_name, model, args.conf, args.foot_offset)


if __name__ == "__main__":
    main()
