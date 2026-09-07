from math import inf
from pathlib import Path
from typing import TypedDict

from PIL import Image
from ultralytics import YOLO  # type: ignore[attr-defined]

from .board_geometry import HexCell
from .board_state_pipeline import hex_key
from .model_adapters import (
    ChampionBox,
    ChampionIdentityCandidate,
    ChampionIdentityPrediction,
    ChampionStarCandidate,
    ChampionStarPrediction,
    HexOccupancyPrediction,
    classify_champion_identity,
    classify_champion_star,
    detect_champion_boxes,
)

DEFAULT_CHAMPION_IDENTITY_IMAGE_SIZE = 160
DEFAULT_CHAMPION_STAR_IMAGE_SIZE = 160
DEFAULT_FOOT_OFFSET_RATIO = 0.0
DEFAULT_STAR_LEFT_PADDING_RATIO = 0.45
DEFAULT_STAR_RIGHT_PADDING_RATIO = 0.08
DEFAULT_STAR_TOP_PADDING_RATIO = 0.60
DEFAULT_STAR_BOTTOM_PADDING_RATIO = 0.05


class ChampionHexAssignment(TypedDict):
    box: ChampionBox
    point_x: float
    point_y: float
    hex: HexCell


class ChampionHexEvidence(TypedDict):
    box: ChampionBox
    point_x: float
    point_y: float
    chosen_key: tuple[int, int]
    occupied_candidate_keys: list[tuple[int, int]]
    champion_name: str
    identity_confidence: float
    identity_candidates: list[ChampionIdentityCandidate]
    star_label: str
    star_confidence: float
    star_candidates: list[ChampionStarCandidate]


class ChampionHexEvidenceSummary(TypedDict):
    confidences_by_hex: dict[tuple[int, int], float]
    champion_names_by_hex: dict[tuple[int, int], str]
    identity_confidences_by_hex: dict[tuple[int, int], float]
    identity_candidates_by_hex: dict[tuple[int, int], list[ChampionIdentityCandidate]]
    star_labels_by_hex: dict[tuple[int, int], str]
    star_confidences_by_hex: dict[tuple[int, int], float]
    star_candidates_by_hex: dict[tuple[int, int], list[ChampionStarCandidate]]
    suppressed_occupancy_keys: set[tuple[int, int]]
    champion_evidence: list[ChampionHexEvidence]


def predict_champion_boxes(
    image_path: Path,
    model: YOLO,
    confidence: float,
) -> list[ChampionBox]:
    return detect_champion_boxes(image_path, model, confidence)


def box_bottom_center(
    box: ChampionBox,
    image_height: int,
    foot_offset_ratio: float,
) -> tuple[float, float]:
    box_height = box["y2"] - box["y1"]
    point_x = (box["x1"] + box["x2"]) / 2
    point_y = min(box["y2"] + box_height * foot_offset_ratio, image_height - 1)
    return (point_x, point_y)


def squared_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return (x1 - x2) ** 2 + (y1 - y2) ** 2


def find_nearest_hex(point_x: float, point_y: float, hexes: list[HexCell]) -> HexCell:
    best_hex = hexes[0]
    best_distance = inf

    for hex_cell in hexes:
        distance = squared_distance(
            point_x,
            point_y,
            hex_cell["center_x"],
            hex_cell["center_y"],
        )

        if distance < best_distance:
            best_hex = hex_cell
            best_distance = distance

    return best_hex


def assign_champions_to_hexes(
    champion_boxes: list[ChampionBox],
    hexes: list[HexCell],
    image_height: int,
    foot_offset_ratio: float,
) -> list[ChampionHexAssignment]:
    assignments: list[ChampionHexAssignment] = []

    for box in champion_boxes:
        point_x, point_y = box_bottom_center(box, image_height, foot_offset_ratio)
        nearest_hex = find_nearest_hex(point_x, point_y, hexes)
        assignments.append(
            {
                "box": box,
                "point_x": point_x,
                "point_y": point_y,
                "hex": nearest_hex,
            }
        )

    return assignments


def create_occupancy_predictions_by_hex(
    occupancy_predictions: list[HexOccupancyPrediction],
) -> dict[tuple[int, int], HexOccupancyPrediction]:
    return {
        hex_key(prediction["row"], prediction["column"]): prediction
        for prediction in occupancy_predictions
    }


def hex_center_is_inside_champion_box(hex_cell: HexCell, box: ChampionBox) -> bool:
    return (
        box["x1"] <= hex_cell["center_x"] <= box["x2"]
        and box["y1"] <= hex_cell["center_y"] <= box["y2"]
    )


def find_best_hex_for_champion_box(
    box: ChampionBox,
    hexes: list[HexCell],
    occupied_hex_keys: set[tuple[int, int]],
    image_height: int,
    foot_offset_ratio: float,
) -> tuple[HexCell, list[HexCell], tuple[float, float]]:
    point_x, point_y = box_bottom_center(box, image_height, foot_offset_ratio)
    occupied_hexes_under_box = [
        hex_cell
        for hex_cell in hexes
        if hex_key(hex_cell["row"], hex_cell["column"]) in occupied_hex_keys
        and hex_center_is_inside_champion_box(hex_cell, box)
    ]

    if len(occupied_hexes_under_box) > 0:
        return (
            find_nearest_hex(point_x, point_y, occupied_hexes_under_box),
            occupied_hexes_under_box,
            (point_x, point_y),
        )

    return (find_nearest_hex(point_x, point_y, hexes), [], (point_x, point_y))


def crop_champion_box(
    board_image: Image.Image,
    box: ChampionBox,
    padding_ratio: float,
) -> Image.Image:
    box_width = box["x2"] - box["x1"]
    box_height = box["y2"] - box["y1"]
    x_padding = box_width * padding_ratio
    y_padding = box_height * padding_ratio
    x1 = max(0, int(round(box["x1"] - x_padding)))
    y1 = max(0, int(round(box["y1"] - y_padding)))
    x2 = min(board_image.width, int(round(box["x2"] + x_padding)))
    y2 = min(board_image.height, int(round(box["y2"] + y_padding)))

    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"Invalid champion box: {box}")

    return board_image.crop((x1, y1, x2, y2)).convert("RGB")


def crop_champion_star_box(
    board_image: Image.Image,
    box: ChampionBox,
    left_padding_ratio: float = DEFAULT_STAR_LEFT_PADDING_RATIO,
    right_padding_ratio: float = DEFAULT_STAR_RIGHT_PADDING_RATIO,
    top_padding_ratio: float = DEFAULT_STAR_TOP_PADDING_RATIO,
    bottom_padding_ratio: float = DEFAULT_STAR_BOTTOM_PADDING_RATIO,
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


def classify_champion_crop(
    crop: Image.Image,
    identity_model: YOLO,
    image_size: int = DEFAULT_CHAMPION_IDENTITY_IMAGE_SIZE,
) -> ChampionIdentityPrediction:
    return classify_champion_identity(crop, identity_model, image_size)


def classify_champion_star_crop(
    crop: Image.Image,
    star_model: YOLO,
    image_size: int = DEFAULT_CHAMPION_STAR_IMAGE_SIZE,
) -> ChampionStarPrediction:
    return classify_champion_star(crop, star_model, image_size)


def get_champion_hex_evidence(
    board_crop_path: Path,
    champion_model: YOLO,
    identity_model: YOLO,
    star_model: YOLO,
    champion_confidence: float,
    identity_padding_ratio: float,
    foot_offset_ratio: float,
    hexes: list[HexCell],
    occupancy_predictions: list[HexOccupancyPrediction],
) -> ChampionHexEvidenceSummary:
    board_image = Image.open(board_crop_path).convert("RGB")
    champion_boxes = predict_champion_boxes(
        board_crop_path,
        champion_model,
        champion_confidence,
    )
    occupancy_predictions_by_hex = create_occupancy_predictions_by_hex(occupancy_predictions)
    occupied_hex_keys = {
        key for key, prediction in occupancy_predictions_by_hex.items() if prediction["occupied"]
    }
    confidences_by_hex: dict[tuple[int, int], float] = {}
    champion_names_by_hex: dict[tuple[int, int], str] = {}
    identity_confidences_by_hex: dict[tuple[int, int], float] = {}
    identity_candidates_by_hex: dict[tuple[int, int], list[ChampionIdentityCandidate]] = {}
    star_labels_by_hex: dict[tuple[int, int], str] = {}
    star_confidences_by_hex: dict[tuple[int, int], float] = {}
    star_candidates_by_hex: dict[tuple[int, int], list[ChampionStarCandidate]] = {}
    suppressed_occupancy_keys: set[tuple[int, int]] = set()
    champion_evidence: list[ChampionHexEvidence] = []

    for box in champion_boxes:
        identity_prediction = classify_champion_crop(
            crop_champion_box(board_image, box, identity_padding_ratio),
            identity_model,
        )
        star_prediction = classify_champion_star_crop(
            crop_champion_star_box(board_image, box),
            star_model,
        )
        assigned_hex, occupied_hexes_under_box, point = find_best_hex_for_champion_box(
            box,
            hexes,
            occupied_hex_keys,
            board_image.height,
            foot_offset_ratio,
        )
        key = hex_key(assigned_hex["row"], assigned_hex["column"])
        occupied_candidate_keys = [
            hex_key(hex_cell["row"], hex_cell["column"]) for hex_cell in occupied_hexes_under_box
        ]
        previous_confidence = confidences_by_hex.get(key, 0.0)

        if box["confidence"] >= previous_confidence:
            confidences_by_hex[key] = box["confidence"]
            champion_names_by_hex[key] = identity_prediction["champion_name"]
            identity_confidences_by_hex[key] = identity_prediction["confidence"]
            identity_candidates_by_hex[key] = identity_prediction["candidates"]
            star_labels_by_hex[key] = star_prediction["star_label"]
            star_confidences_by_hex[key] = star_prediction["confidence"]
            star_candidates_by_hex[key] = star_prediction["candidates"]

        suppressed_occupancy_keys.update(
            candidate_key for candidate_key in occupied_candidate_keys if candidate_key != key
        )
        champion_evidence.append(
            {
                "box": box,
                "point_x": point[0],
                "point_y": point[1],
                "chosen_key": key,
                "occupied_candidate_keys": occupied_candidate_keys,
                "champion_name": identity_prediction["champion_name"],
                "identity_confidence": identity_prediction["confidence"],
                "identity_candidates": identity_prediction["candidates"],
                "star_label": star_prediction["star_label"],
                "star_confidence": star_prediction["confidence"],
                "star_candidates": star_prediction["candidates"],
            }
        )

    return {
        "confidences_by_hex": confidences_by_hex,
        "champion_names_by_hex": champion_names_by_hex,
        "identity_confidences_by_hex": identity_confidences_by_hex,
        "identity_candidates_by_hex": identity_candidates_by_hex,
        "star_labels_by_hex": star_labels_by_hex,
        "star_confidences_by_hex": star_confidences_by_hex,
        "star_candidates_by_hex": star_candidates_by_hex,
        "suppressed_occupancy_keys": suppressed_occupancy_keys,
        "champion_evidence": champion_evidence,
    }
