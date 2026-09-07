import argparse
import json
import shutil
from pathlib import Path
from typing import TypedDict

import _bootstrap  # noqa: F401
from combine_hex_signals import CHAMPION_CONFIDENCE, CHAMPION_MODEL_PATH, CROPS_DIR
from PIL import Image
from ultralytics import YOLO  # type: ignore[attr-defined]

from board_detector.champion_hex_evidence import predict_champion_boxes
from board_detector.model_adapters import ChampionBox

OUTPUT_DIR = Path("data/champion-star/source")
MANIFEST_PATH = Path("data/champion-star/star-crops-manifest.json")
DEFAULT_LEFT_PADDING_RATIO = 0.45
DEFAULT_RIGHT_PADDING_RATIO = 0.08
DEFAULT_TOP_PADDING_RATIO = 0.60
DEFAULT_BOTTOM_PADDING_RATIO = 0.05


class ChampionStarCropRecord(TypedDict):
    source_image: str
    crop_path: str
    detector_confidence: float
    box: ChampionBox


def crop_champion_star_box(
    board_image: Image.Image,
    box: ChampionBox,
    left_padding_ratio: float,
    right_padding_ratio: float,
    top_padding_ratio: float,
    bottom_padding_ratio: float,
) -> Image.Image:
    box_width = box["x2"] - box["x1"]
    box_height = box["y2"] - box["y1"]
    left_padding = box_width * left_padding_ratio
    right_padding = box_width * right_padding_ratio
    top_padding = box_height * top_padding_ratio
    bottom_padding = box_height * bottom_padding_ratio
    x1 = max(0, int(round(box["x1"] - left_padding)))
    y1 = max(0, int(round(box["y1"] - top_padding)))
    x2 = min(board_image.width, int(round(box["x2"] + right_padding)))
    y2 = min(board_image.height, int(round(box["y2"] + bottom_padding)))

    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"Invalid champion star box: {box}")

    return board_image.crop((x1, y1, x2, y2)).convert("RGB")


def crop_file_name(image_name: str, box_index: int, box: ChampionBox) -> str:
    confidence_text = f"{box['confidence']:.2f}".replace(".", "p")
    return f"{Path(image_name).stem}_box_{box_index:03d}_conf_{confidence_text}.png"


def collect_star_crops_for_image(
    image_path: Path,
    champion_model: YOLO,
    champion_confidence: float,
    left_padding_ratio: float,
    right_padding_ratio: float,
    top_padding_ratio: float,
    bottom_padding_ratio: float,
) -> list[ChampionStarCropRecord]:
    board_image = Image.open(image_path).convert("RGB")
    champion_boxes = predict_champion_boxes(image_path, champion_model, champion_confidence)
    records: list[ChampionStarCropRecord] = []

    for box_index, box in enumerate(champion_boxes):
        crop = crop_champion_star_box(
            board_image,
            box,
            left_padding_ratio,
            right_padding_ratio,
            top_padding_ratio,
            bottom_padding_ratio,
        )
        crop_path = OUTPUT_DIR / crop_file_name(image_path.name, box_index, box)
        crop_path.parent.mkdir(parents=True, exist_ok=True)
        crop.save(crop_path)
        records.append(
            {
                "source_image": image_path.name,
                "crop_path": str(crop_path),
                "detector_confidence": box["confidence"],
                "box": box,
            }
        )

    return records


def collect_star_crops(
    image_paths: list[Path],
    champion_confidence: float,
    left_padding_ratio: float,
    right_padding_ratio: float,
    top_padding_ratio: float,
    bottom_padding_ratio: float,
    clear_existing: bool,
) -> list[ChampionStarCropRecord]:
    if clear_existing and OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    champion_model = YOLO(CHAMPION_MODEL_PATH)
    existing_records: list[ChampionStarCropRecord] = []
    if not clear_existing and MANIFEST_PATH.exists():
        existing_records = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    refreshed_image_names = {image_path.name for image_path in image_paths}
    records = [
        record
        for record in existing_records
        if record["source_image"] not in refreshed_image_names
    ]

    for index, image_path in enumerate(image_paths, start=1):
        image_records = collect_star_crops_for_image(
            image_path,
            champion_model,
            champion_confidence,
            left_padding_ratio,
            right_padding_ratio,
            top_padding_ratio,
            bottom_padding_ratio,
        )
        records.extend(image_records)
        print(f"{index}/{len(image_paths)} {image_path.name}: {len(image_records)} star crops")

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image_name", nargs="?")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--start-index", type=int)
    parser.add_argument("--end-index", type=int)
    parser.add_argument("--champion-conf", type=float, default=CHAMPION_CONFIDENCE)
    parser.add_argument("--left-padding", type=float, default=DEFAULT_LEFT_PADDING_RATIO)
    parser.add_argument("--right-padding", type=float, default=DEFAULT_RIGHT_PADDING_RATIO)
    parser.add_argument("--top-padding", type=float, default=DEFAULT_TOP_PADDING_RATIO)
    parser.add_argument("--bottom-padding", type=float, default=DEFAULT_BOTTOM_PADDING_RATIO)
    parser.add_argument("--keep-existing", action="store_true")
    args = parser.parse_args()

    if args.start_index is not None or args.end_index is not None:
        if args.start_index is None or args.end_index is None:
            raise ValueError("--start-index and --end-index must be used together")
        image_paths = [
            CROPS_DIR / f"image_{index}.png"
            for index in range(args.start_index, args.end_index + 1)
        ]
        missing_paths = [path for path in image_paths if not path.exists()]
        if len(missing_paths) > 0:
            raise FileNotFoundError(f"Missing board crops: {missing_paths}")
    elif args.all:
        image_paths = sorted(CROPS_DIR.glob("*.png"))
    else:
        image_name = args.image_name or "image_388.png"
        image_paths = [CROPS_DIR / image_name]

    if len(image_paths) == 0:
        raise FileNotFoundError(f"No board crops found in: {CROPS_DIR}")

    records = collect_star_crops(
        image_paths,
        args.champion_conf,
        args.left_padding,
        args.right_padding,
        args.top_padding,
        args.bottom_padding,
        clear_existing=not args.keep_existing,
    )
    print(f"star_crops: {len(records)}")
    print(f"saved: {OUTPUT_DIR}")
    print(f"manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
