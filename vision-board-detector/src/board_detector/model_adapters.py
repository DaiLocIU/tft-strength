from pathlib import Path
from typing import Any, Optional, TypedDict, cast

from PIL import Image
from ultralytics import YOLO  # type: ignore[attr-defined]

from .board_geometry import HexCell, crop_hex_patch


class BoardDetection(TypedDict):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float


class ChampionBox(TypedDict):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float


class HexOccupancyPrediction(TypedDict):
    row: int
    column: int
    class_name: str
    confidence: float
    occupied: bool


class ChampionIdentityCandidate(TypedDict):
    champion_name: str
    confidence: float


class ChampionIdentityPrediction(TypedDict):
    champion_name: str
    confidence: float
    candidates: list[ChampionIdentityCandidate]


class ChampionStarCandidate(TypedDict):
    star_label: str
    confidence: float


class ChampionStarPrediction(TypedDict):
    star_label: str
    confidence: float
    candidates: list[ChampionStarCandidate]


def to_list(values: Any) -> list[Any]:
    if hasattr(values, "tolist"):
        return cast(list[Any], values.tolist())

    return list(values)


def detect_board_box(
    image_path: Path,
    model: YOLO,
) -> Optional[BoardDetection]:
    results = cast(list[Any], model(image_path, verbose=False))
    boxes = results[0].boxes

    if boxes is None or len(boxes) == 0:
        return None

    best_index = int(boxes.conf.argmax())
    x1, y1, x2, y2 = boxes.xyxy[best_index].tolist()

    return {
        "x1": float(x1),
        "y1": float(y1),
        "x2": float(x2),
        "y2": float(y2),
        "confidence": float(boxes.conf[best_index]),
    }


def detect_champion_boxes(
    image_path: Path,
    model: YOLO,
    confidence: float,
) -> list[ChampionBox]:
    results = cast(list[Any], model(str(image_path), conf=confidence, verbose=False))
    boxes = results[0].boxes

    if boxes is None or len(boxes) == 0:
        return []

    champion_boxes: list[ChampionBox] = []

    for index in range(len(boxes)):
        x1, y1, x2, y2 = boxes.xyxy[index].tolist()
        champion_boxes.append(
            {
                "x1": float(x1),
                "y1": float(y1),
                "x2": float(x2),
                "y2": float(y2),
                "confidence": float(boxes.conf[index]),
            }
        )

    return champion_boxes


def classify_hex_occupancy(
    model: YOLO,
    board_image: Image.Image,
    hex_cell: HexCell,
    image_size: int,
    occupied_confidence_threshold: float,
) -> HexOccupancyPrediction:
    patch = crop_hex_patch(board_image, hex_cell)
    results = cast(list[Any], model(patch, imgsz=image_size, verbose=False))
    result = results[0]
    probs = result.probs

    if probs is None:
        raise ValueError("Classifier result did not include probabilities.")

    class_index = int(probs.top1)
    class_name = str(result.names[class_index])
    confidence = float(probs.top1conf)

    return {
        "row": hex_cell["row"],
        "column": hex_cell["column"],
        "class_name": class_name,
        "confidence": confidence,
        "occupied": class_name == "occupied" and confidence >= occupied_confidence_threshold,
    }


def classify_champion_identity(
    crop: Image.Image,
    model: YOLO,
    image_size: int,
) -> ChampionIdentityPrediction:
    results = cast(list[Any], model(crop, imgsz=image_size, verbose=False))
    result = results[0]
    probs = result.probs

    if probs is None:
        raise ValueError("Champion identity result did not include probabilities.")

    class_index = int(probs.top1)
    champion_name = str(result.names[class_index])
    top_indexes = [int(index) for index in to_list(probs.top5)]
    top_confidences = [float(confidence) for confidence in to_list(probs.top5conf)]
    candidates = [
        {
            "champion_name": str(result.names[index]),
            "confidence": confidence,
        }
        for index, confidence in zip(top_indexes, top_confidences)
    ]

    return {
        "champion_name": champion_name,
        "confidence": float(probs.top1conf),
        "candidates": candidates,
    }


def classify_champion_star(
    crop: Image.Image,
    model: YOLO,
    image_size: int,
) -> ChampionStarPrediction:
    results = cast(list[Any], model(crop, imgsz=image_size, verbose=False))
    result = results[0]
    probs = result.probs

    if probs is None:
        raise ValueError("Champion star result did not include probabilities.")

    class_index = int(probs.top1)
    star_label = str(result.names[class_index])
    top_indexes = [int(index) for index in to_list(probs.top5)]
    top_confidences = [float(confidence) for confidence in to_list(probs.top5conf)]
    candidates = [
        {
            "star_label": str(result.names[index]),
            "confidence": confidence,
        }
        for index, confidence in zip(top_indexes, top_confidences)
    ]

    return {
        "star_label": star_label,
        "confidence": float(probs.top1conf),
        "candidates": candidates,
    }
