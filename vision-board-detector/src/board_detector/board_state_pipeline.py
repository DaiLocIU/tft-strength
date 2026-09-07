from typing import Any, Literal, Optional, TypedDict

from .model_adapters import ChampionIdentityCandidate, ChampionStarCandidate, HexOccupancyPrediction

SignalSource = Literal["both", "occupancy_only", "champion_only", "empty"]

# Identity models are trained from asset folders, whose identifiers do not
# always match the champion name shown to players.
CHAMPION_NAME_ALIASES = {
    "ancient_sentinel": "Sentinel",
}


def normalize_champion_name(name: Optional[str]) -> Optional[str]:
    if name is None:
        return None
    return CHAMPION_NAME_ALIASES.get(name.casefold().replace(" ", "_"), name)


class CombinedHexSignal(TypedDict):
    row: int
    column: int
    occupied: bool
    source: SignalSource
    occupancy_confidence: Optional[float]
    champion_confidence: Optional[float]
    champion_name: Optional[str]
    raw_champion_name: Optional[str]
    identity_confidence: Optional[float]
    identity_candidates: list[ChampionIdentityCandidate]
    star: Optional[str]
    star_confidence: Optional[float]
    star_candidates: list[ChampionStarCandidate]
    needs_review: bool
    review_reason: Optional[str]


class BoardStateConfig(TypedDict):
    champion_confidence: float
    identity_padding_ratio: float
    identity_confidence_threshold: float


def hex_key(row: int, column: int) -> tuple[int, int]:
    return (row, column)


def combine_predictions(
    occupancy_predictions: list[HexOccupancyPrediction],
    champion_confidences_by_hex: dict[tuple[int, int], float],
    champion_names_by_hex: dict[tuple[int, int], str],
    identity_confidences_by_hex: dict[tuple[int, int], float],
    identity_candidates_by_hex: dict[tuple[int, int], list[ChampionIdentityCandidate]],
    star_labels_by_hex: dict[tuple[int, int], str],
    star_confidences_by_hex: dict[tuple[int, int], float],
    star_candidates_by_hex: dict[tuple[int, int], list[ChampionStarCandidate]],
    suppressed_occupancy_keys: set[tuple[int, int]],
    identity_confidence_threshold: float,
) -> list[CombinedHexSignal]:
    combined_signals: list[CombinedHexSignal] = []

    for prediction in occupancy_predictions:
        key = hex_key(prediction["row"], prediction["column"])
        champion_confidence = champion_confidences_by_hex.get(key)
        raw_champion_name = champion_names_by_hex.get(key)
        identity_confidence = identity_confidences_by_hex.get(key)
        identity_candidates = identity_candidates_by_hex.get(key, [])
        star = star_labels_by_hex.get(key)
        star_confidence = star_confidences_by_hex.get(key)
        star_candidates = star_candidates_by_hex.get(key, [])
        champion_mapped = champion_confidence is not None
        occupancy_occupied = prediction["occupied"] and (
            key not in suppressed_occupancy_keys or champion_mapped
        )
        needs_review = False
        review_reason: Optional[str] = None
        champion_name = normalize_champion_name(raw_champion_name)
        identity_candidates = [
            {
                **candidate,
                "champion_name": normalize_champion_name(candidate["champion_name"]),
            }
            for candidate in identity_candidates
        ]

        if (
            champion_mapped
            and identity_confidence is not None
            and identity_confidence < identity_confidence_threshold
        ):
            champion_name = "unknown"
            needs_review = True
            review_reason = "low_identity_confidence"

        if occupancy_occupied and champion_mapped:
            source: SignalSource = "both"
        elif occupancy_occupied:
            source = "occupancy_only"
        elif champion_mapped:
            source = "champion_only"
        else:
            source = "empty"

        combined_signals.append(
            {
                "row": prediction["row"],
                "column": prediction["column"],
                "occupied": occupancy_occupied or champion_mapped,
                "source": source,
                "occupancy_confidence": prediction["confidence"],
                "champion_confidence": champion_confidence,
                "champion_name": champion_name,
                "raw_champion_name": raw_champion_name,
                "identity_confidence": identity_confidence,
                "identity_candidates": identity_candidates,
                "star": star,
                "star_confidence": star_confidence,
                "star_candidates": star_candidates,
                "needs_review": needs_review,
                "review_reason": review_reason,
            }
        )

    return combined_signals


def create_board_state(
    image_name: str,
    combined_signals: list[CombinedHexSignal],
    config: BoardStateConfig,
) -> dict[str, Any]:
    occupied_units = [
        {
            "row": signal["row"],
            "column": signal["column"],
            "champion": signal["champion_name"] or "unknown",
            "raw_champion": signal["raw_champion_name"],
            "source": signal["source"],
            "occupancy_confidence": signal["occupancy_confidence"],
            "champion_confidence": signal["champion_confidence"],
            "identity_confidence": signal["identity_confidence"],
            "identity_candidates": signal["identity_candidates"],
            "star": signal["star"] or "unknown",
            "star_confidence": signal["star_confidence"],
            "star_candidates": signal["star_candidates"],
            "needs_review": signal["needs_review"],
            "review_reason": signal["review_reason"],
        }
        for signal in combined_signals
        if signal["occupied"]
    ]
    missing_hexes = [
        {
            "row": signal["row"],
            "column": signal["column"],
            "reason": "occupied_without_champion_box",
            "occupancy_confidence": signal["occupancy_confidence"],
        }
        for signal in combined_signals
        if signal["occupied"] and signal["source"] == "occupancy_only"
    ]

    return {
        "image_name": image_name,
        "units": occupied_units,
        "review": {
            "identity_confidence_threshold": config["identity_confidence_threshold"],
            "low_identity_confidence": [
                unit
                for unit in occupied_units
                if unit["review_reason"] == "low_identity_confidence"
            ],
            "missing_hexes": missing_hexes,
        },
        "parameters": {
            "champion_confidence": config["champion_confidence"],
            "identity_padding_ratio": config["identity_padding_ratio"],
            "identity_confidence_threshold": config["identity_confidence_threshold"],
        },
    }
