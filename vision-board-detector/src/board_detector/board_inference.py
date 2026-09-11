import argparse
import json
from pathlib import Path
from typing import Union

from PIL import Image, ImageDraw, ImageFont
from board_detector.hex_occupancy import (
    MODEL_PATH as HEX_OCCUPANCY_MODEL_PATH,
)
from board_detector.hex_occupancy import predict_board_hex_occupancy
from ultralytics import YOLO  # type: ignore[attr-defined]

from board_detector.board_geometry import (
    HexCell,
    create_board_hex_cells,
    create_hex_polygon,
    make_tuning_for_image,
)
from board_detector.board_state_pipeline import (
    BoardStateConfig,
    CombinedHexSignal,
    SignalSource,
    combine_predictions,
    create_board_state,
    hex_key,
)
from board_detector.champion_hex_evidence import (
    DEFAULT_FOOT_OFFSET_RATIO,
    ChampionHexEvidence,
    get_champion_hex_evidence,
)

CROPS_DIR = Path("outputs/board-crops")
OUTPUT_DIR = Path("outputs/combined-hex-signals")
BOARD_STATE_OUTPUT_DIR = Path("outputs/board-state")
HEX_OCCUPANCY_REVIEW_THRESHOLD = 0.5
CHAMPION_MODEL_PATH = Path("models/champion-detector.pt")
CHAMPION_IDENTITY_MODEL_PATH = Path("models/champion-identity-classifier.pt")
CHAMPION_STAR_MODEL_PATH = Path("models/champion-star-classifier.pt")
CHAMPION_CONFIDENCE = 0.5
CHAMPION_IDENTITY_IMAGE_SIZE = 160
CHAMPION_IDENTITY_PADDING_RATIO = 0.08
IDENTITY_CONFIDENCE_THRESHOLD = 0.75
LABEL_FONT_SIZE = 24


def load_label_font() -> Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]:
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]

    for font_path in font_paths:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, LABEL_FONT_SIZE)

    return ImageFont.load_default()


def save_board_state(
    image_name: str,
    combined_signals: list[CombinedHexSignal],
    champion_confidence: float,
    identity_padding_ratio: float,
    identity_confidence_threshold: float,
) -> Path:
    config: BoardStateConfig = {
        "champion_confidence": champion_confidence,
        "identity_padding_ratio": identity_padding_ratio,
        "identity_confidence_threshold": identity_confidence_threshold,
    }
    board_state = create_board_state(
        image_name,
        combined_signals,
        config,
    )
    output_path = BOARD_STATE_OUTPUT_DIR / f"{Path(image_name).stem}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(board_state, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def fill_for_source(source: SignalSource) -> tuple[int, int, int, int]:
    if source == "both":
        return (34, 197, 94, 120)

    if source == "occupancy_only":
        return (249, 115, 22, 120)

    if source == "champion_only":
        return (59, 130, 246, 120)

    return (148, 163, 184, 35)


def outline_for_source(source: SignalSource) -> tuple[int, int, int, int]:
    if source == "both":
        return (22, 163, 74, 255)

    if source == "occupancy_only":
        return (234, 88, 12, 255)

    if source == "champion_only":
        return (37, 99, 235, 255)

    return (100, 116, 139, 130)


def source_label(source: SignalSource) -> str:
    if source == "both":
        return "both"

    if source == "occupancy_only":
        return "occ"

    if source == "champion_only":
        return "champ"

    return "empty"


def draw_text_with_background(
    draw: ImageDraw.ImageDraw,
    position: tuple[float, float],
    text: str,
    font: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont],
) -> None:
    x, y = position
    padding = 4
    bbox = draw.textbbox((x, y), text, font=font)
    draw.rectangle(
        (
            bbox[0] - padding,
            bbox[1] - padding,
            bbox[2] + padding,
            bbox[3] + padding,
        ),
        fill=(0, 0, 0, 175),
    )
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)


def format_hex_key(key: tuple[int, int]) -> str:
    return f"{key[0]},{key[1]}"


def draw_champion_evidence(
    draw: ImageDraw.ImageDraw,
    champion_evidence: list[ChampionHexEvidence],
    font: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont],
) -> None:
    for evidence in champion_evidence:
        box = evidence["box"]
        point_x = evidence["point_x"]
        point_y = evidence["point_y"]
        label = (
            f"{format_hex_key(evidence['chosen_key'])} "
            f"{evidence['champion_name']} "
            f"{evidence['star_label']} - {evidence['identity_confidence']:.2f}"
        )

        draw.rectangle(
            (box["x1"], box["y1"], box["x2"], box["y2"]),
            outline=(250, 204, 21, 255),
            width=4,
        )
        draw.ellipse(
            (point_x - 7, point_y - 7, point_x + 7, point_y + 7),
            fill=(250, 204, 21, 255),
            outline=(0, 0, 0, 255),
            width=2,
        )
        draw_text_with_background(draw, (box["x1"], max(0, box["y1"] - 34)), label, font)


def draw_combined_overlay(
    board_crop_path: Path,
    hexes: list[HexCell],
    combined_signals: list[CombinedHexSignal],
    champion_evidence: list[ChampionHexEvidence],
    output_path: Path,
) -> None:
    image = Image.open(board_crop_path).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = load_label_font()
    combined_by_hex = {
        hex_key(signal["row"], signal["column"]): signal for signal in combined_signals
    }

    draw_champion_evidence(draw, champion_evidence, font)

    for hex_cell in hexes:
        key = hex_key(hex_cell["row"], hex_cell["column"])
        signal = combined_by_hex[key]

        if not signal["occupied"]:
            continue

        polygon = create_hex_polygon(hex_cell)
        source = signal["source"]
        label = f"{hex_cell['row']},{hex_cell['column']}"
        champion_name = signal["champion_name"]
        star = signal["star"]

        if champion_name is not None:
            label = f"{label} {champion_name}"
            if star is not None:
                label = f"{label} {star}"

        draw.polygon(
            polygon,
            fill=fill_for_source(source),
            outline=outline_for_source(source),
            width=4,
        )
        draw_text_with_background(
            draw,
            (hex_cell["center_x"] - hex_cell["radius"] * 0.55, hex_cell["center_y"] - 12),
            label,
            font,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(image, overlay).convert("RGB").save(output_path)


def print_combined_signals(combined_signals: list[CombinedHexSignal]) -> None:
    occupied_signals = [signal for signal in combined_signals if signal["occupied"]]

    if len(occupied_signals) == 0:
        print("No occupied hexes.")
        return

    for signal in occupied_signals:
        text = f"occupied: row={signal['row']} column={signal['column']}"

        if signal["champion_name"] is not None:
            text = (
                f"{text} champion={signal['champion_name']} "
                f"identity_confidence={signal['identity_confidence']:.2f}"
            )
            if signal["star"] is not None and signal["star_confidence"] is not None:
                text = (
                    f"{text} star={signal['star']} "
                    f"star_confidence={signal['star_confidence']:.2f}"
                )

        print(text)


def combine_hex_signals_for_image(
    image_name: str,
    hex_occupancy_model: YOLO,
    champion_model: YOLO,
    identity_model: YOLO,
    star_model: YOLO,
    champion_confidence: float,
    identity_padding_ratio: float,
    identity_confidence_threshold: float,
    foot_offset_ratio: float,
    quiet: bool = False,
) -> list[CombinedHexSignal]:
    board_crop_path = CROPS_DIR / image_name

    if not board_crop_path.exists():
        raise FileNotFoundError(f"Board crop not found: {board_crop_path}")

    hexes = sorted(
        create_board_hex_cells(str(board_crop_path), make_tuning_for_image(image_name)),
        key=lambda hex_cell: (hex_cell["row"], hex_cell["column"]),
    )
    occupancy_predictions = predict_board_hex_occupancy(
        board_crop_path,
        HEX_OCCUPANCY_MODEL_PATH,
        hex_occupancy_model,
    )
    champion_hex_evidence = get_champion_hex_evidence(
        board_crop_path,
        champion_model,
        identity_model,
        star_model,
        champion_confidence,
        identity_padding_ratio,
        foot_offset_ratio,
        hexes,
        occupancy_predictions,
    )
    combined_signals = combine_predictions(
        occupancy_predictions,
        champion_hex_evidence["confidences_by_hex"],
        champion_hex_evidence["champion_names_by_hex"],
        champion_hex_evidence["identity_confidences_by_hex"],
        champion_hex_evidence["identity_candidates_by_hex"],
        champion_hex_evidence["star_labels_by_hex"],
        champion_hex_evidence["star_confidences_by_hex"],
        champion_hex_evidence["star_candidates_by_hex"],
        champion_hex_evidence["suppressed_occupancy_keys"],
        identity_confidence_threshold,
    )
    output_path = OUTPUT_DIR / f"{Path(image_name).stem}-combined-hex-signals.png"
    board_state_path = save_board_state(
        image_name,
        combined_signals,
        champion_confidence,
        identity_padding_ratio,
        identity_confidence_threshold,
    )

    draw_combined_overlay(
        board_crop_path,
        hexes,
        combined_signals,
        champion_hex_evidence["champion_evidence"],
        output_path,
    )

    if quiet:
        return combined_signals

    print_combined_signals(combined_signals)
    print(f"saved: {output_path}")
    print(f"json: {board_state_path}")

    return combined_signals


def combine_all_board_crops(
    champion_confidence: float,
    identity_padding_ratio: float,
    identity_confidence_threshold: float,
    foot_offset_ratio: float,
) -> None:
    board_crop_paths = sorted(CROPS_DIR.glob("*.png"))

    if len(board_crop_paths) == 0:
        raise FileNotFoundError(f"No board crops found in: {CROPS_DIR}")

    hex_occupancy_model = YOLO(HEX_OCCUPANCY_MODEL_PATH)
    champion_model = YOLO(CHAMPION_MODEL_PATH)
    identity_model = YOLO(CHAMPION_IDENTITY_MODEL_PATH)
    star_model = YOLO(CHAMPION_STAR_MODEL_PATH)
    total_occupied = 0

    for index, board_crop_path in enumerate(board_crop_paths, start=1):
        combined_signals = combine_hex_signals_for_image(
            board_crop_path.name,
            hex_occupancy_model,
            champion_model,
            identity_model,
            star_model,
            champion_confidence,
            identity_padding_ratio,
            identity_confidence_threshold,
            foot_offset_ratio,
            quiet=True,
        )
        occupied_count = len([signal for signal in combined_signals if signal["occupied"]])
        total_occupied += occupied_count
        print(f"{index}/{len(board_crop_paths)} {board_crop_path.name}: {occupied_count} occupied")

    print(f"images: {len(board_crop_paths)}")
    print(f"occupied: {total_occupied}")
    print(f"saved: {OUTPUT_DIR}")
    print(f"json: {BOARD_STATE_OUTPUT_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image_name", nargs="?", default="image_1.png")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--champion-conf", type=float, default=CHAMPION_CONFIDENCE)
    parser.add_argument(
        "--identity-padding",
        type=float,
        default=CHAMPION_IDENTITY_PADDING_RATIO,
    )
    parser.add_argument("--identity-conf", type=float, default=IDENTITY_CONFIDENCE_THRESHOLD)
    parser.add_argument("--foot-offset", type=float, default=DEFAULT_FOOT_OFFSET_RATIO)
    args = parser.parse_args()

    if args.all:
        combine_all_board_crops(
            args.champion_conf,
            args.identity_padding,
            args.identity_conf,
            args.foot_offset,
        )
        return

    hex_occupancy_model = YOLO(HEX_OCCUPANCY_MODEL_PATH)
    champion_model = YOLO(CHAMPION_MODEL_PATH)
    identity_model = YOLO(CHAMPION_IDENTITY_MODEL_PATH)
    star_model = YOLO(CHAMPION_STAR_MODEL_PATH)
    combine_hex_signals_for_image(
        args.image_name,
        hex_occupancy_model,
        champion_model,
        identity_model,
        star_model,
        args.champion_conf,
        args.identity_padding,
        args.identity_conf,
        args.foot_offset,
    )


if __name__ == "__main__":
    main()
