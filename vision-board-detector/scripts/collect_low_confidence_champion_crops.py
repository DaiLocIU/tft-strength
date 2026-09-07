import argparse
import json
import shutil
from pathlib import Path
from typing import TypedDict

import _bootstrap  # noqa: F401
from combine_hex_signals import (
    CHAMPION_CONFIDENCE,
    CHAMPION_IDENTITY_MODEL_PATH,
    CHAMPION_IDENTITY_PADDING_RATIO,
    CHAMPION_MODEL_PATH,
    CROPS_DIR,
)
from PIL import Image
from ultralytics import YOLO  # type: ignore[attr-defined]

from board_detector.champion_hex_evidence import (
    classify_champion_crop,
    crop_champion_box,
    predict_champion_boxes,
)
from board_detector.model_adapters import ChampionBox, ChampionIdentityPrediction

OUTPUT_DIR = Path("data/champion-identity/review-low-confidence")
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"
LOW_CONFIDENCE_THRESHOLD = 0.75


class LowConfidenceCropRecord(TypedDict):
    source_image: str
    crop_path: str
    predicted_name: str
    identity_confidence: float
    detector_confidence: float
    box: ChampionBox


def safe_folder_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def crop_file_name(
    image_name: str,
    box_index: int,
    prediction: ChampionIdentityPrediction,
) -> str:
    image_stem = Path(image_name).stem
    confidence_text = f"{prediction['confidence']:.2f}".replace(".", "p")
    name = safe_folder_name(prediction["champion_name"])
    return f"{image_stem}_box_{box_index:02d}_{name}_{confidence_text}.png"


def save_low_confidence_crops(
    image_path: Path,
    champion_model: YOLO,
    identity_model: YOLO,
    champion_confidence: float,
    identity_padding_ratio: float,
    low_confidence_threshold: float,
) -> list[LowConfidenceCropRecord]:
    board_image = Image.open(image_path).convert("RGB")
    champion_boxes = predict_champion_boxes(image_path, champion_model, champion_confidence)
    records: list[LowConfidenceCropRecord] = []

    for box_index, box in enumerate(champion_boxes):
        crop = crop_champion_box(board_image, box, identity_padding_ratio)
        prediction = classify_champion_crop(crop, identity_model)

        if prediction["confidence"] >= low_confidence_threshold:
            continue

        predicted_folder = OUTPUT_DIR / safe_folder_name(prediction["champion_name"])
        predicted_folder.mkdir(parents=True, exist_ok=True)
        crop_path = predicted_folder / crop_file_name(image_path.name, box_index, prediction)
        crop.save(crop_path)
        records.append(
            {
                "source_image": image_path.name,
                "crop_path": str(crop_path),
                "predicted_name": prediction["champion_name"],
                "identity_confidence": prediction["confidence"],
                "detector_confidence": box["confidence"],
                "box": box,
            }
        )

    return records


def collect_low_confidence_crops(
    image_paths: list[Path],
    champion_confidence: float,
    identity_padding_ratio: float,
    low_confidence_threshold: float,
    clear_existing: bool,
) -> list[LowConfidenceCropRecord]:
    if clear_existing and OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    champion_model = YOLO(CHAMPION_MODEL_PATH)
    identity_model = YOLO(CHAMPION_IDENTITY_MODEL_PATH)
    records: list[LowConfidenceCropRecord] = []

    for index, image_path in enumerate(image_paths, start=1):
        image_records = save_low_confidence_crops(
            image_path,
            champion_model,
            identity_model,
            champion_confidence,
            identity_padding_ratio,
            low_confidence_threshold,
        )
        records.extend(image_records)
        print(f"{index}/{len(image_paths)} {image_path.name}: {len(image_records)} low confidence")

    MANIFEST_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image_name", nargs="?")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--champion-conf", type=float, default=CHAMPION_CONFIDENCE)
    parser.add_argument("--identity-padding", type=float, default=CHAMPION_IDENTITY_PADDING_RATIO)
    parser.add_argument("--threshold", type=float, default=LOW_CONFIDENCE_THRESHOLD)
    parser.add_argument("--keep-existing", action="store_true")
    args = parser.parse_args()

    if args.all:
        image_paths = sorted(CROPS_DIR.glob("*.png"))
    else:
        image_name = args.image_name or "image_388.png"
        image_paths = [CROPS_DIR / image_name]

    if len(image_paths) == 0:
        raise FileNotFoundError(f"No board crops found in: {CROPS_DIR}")

    records = collect_low_confidence_crops(
        image_paths,
        args.champion_conf,
        args.identity_padding,
        args.threshold,
        clear_existing=not args.keep_existing,
    )
    print(f"low_confidence_crops: {len(records)}")
    print(f"saved: {OUTPUT_DIR}")
    print(f"manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
