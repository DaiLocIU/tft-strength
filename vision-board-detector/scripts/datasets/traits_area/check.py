"""Validate a Label Studio export for active-traits-area detection.

This is a preflight check only: unlike ``check_dataset.py`` it does not copy
images or create YOLO labels.  Run it before converting the export so that
every training image is present and has exactly one usable active-traits-area
rectangle.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any, Optional, TypedDict, cast

TRAITS_LABEL = "active_traits"


class VerifyResult(TypedDict):
    matched: list[str]
    missing: list[str]
    valid_labels: list[str]
    bad_labels: dict[str, str]


def original_filename(label_studio_path: str) -> str:
    """Remove the upload UUID which Label Studio adds to imported filenames."""
    internal_filename = Path(label_studio_path).name
    return re.sub(r"^[0-9a-f]{8}-", "", internal_filename)


def find_traits_rectangles(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Return all rectangle labels marked as the active-traits area."""
    rectangles: list[dict[str, Any]] = []
    for annotation in task.get("annotations", []):
        if annotation.get("was_cancelled"):
            continue
        for result in annotation.get("result", []):
            value = result.get("value", {})
            if (
                result.get("type") == "rectanglelabels"
                and TRAITS_LABEL in value.get("rectanglelabels", [])
            ):
                rectangles.append(value)
    return rectangles


def rectangle_error(rectangle: dict[str, Any]) -> Optional[str]:
    """Validate Label Studio's percentage-based rectangle coordinates."""
    required_fields = ("x", "y", "width", "height")
    try:
        x, y, width, height = (float(rectangle[field]) for field in required_fields)
    except (KeyError, TypeError, ValueError):
        return "rectangle is missing numeric x, y, width, or height"

    if width <= 0 or height <= 0:
        return "rectangle width and height must be greater than zero"
    if x < 0 or y < 0 or x + width > 100 or y + height > 100:
        return "rectangle extends outside the image bounds"
    return None


def verify_traits_area_labels(export_path: str, raw_dir: str) -> VerifyResult:
    """Check that each task has an image and one valid active-traits rectangle."""
    export_file = Path(export_path)
    raw_path = Path(raw_dir)
    tasks = cast(list[dict[str, Any]], json.loads(export_file.read_text(encoding="utf-8")))

    matched: list[str] = []
    missing: list[str] = []
    valid_labels: list[str] = []
    bad_labels: dict[str, str] = {}

    for task in tasks:
        image_path_value = task.get("data", {}).get("image")
        if not isinstance(image_path_value, str):
            bad_labels[f"task-{task.get('id', 'unknown')}"] = "task has no image path"
            continue

        filename = original_filename(image_path_value)
        if (raw_path / filename).is_file():
            matched.append(filename)
        else:
            missing.append(filename)

        rectangles = find_traits_rectangles(task)
        if len(rectangles) != 1:
            bad_labels[filename] = (
                f"expected exactly one {TRAITS_LABEL!r} rectangle; found {len(rectangles)}"
            )
            continue

        error = rectangle_error(rectangles[0])
        if error:
            bad_labels[filename] = error
            continue

        valid_labels.append(filename)

    return {
        "matched": matched,
        "missing": missing,
        "valid_labels": valid_labels,
        "bad_labels": bad_labels,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--export",
        default="exports/label-studio/traits-area.json",
        help="Label Studio JSON export to validate",
    )
    parser.add_argument(
        "--raw-dir",
        default="data/raw",
        help="Directory containing the original screenshot files",
    )
    args = parser.parse_args()

    result = verify_traits_area_labels(args.export, args.raw_dir)
    print(f"matched: {len(result['matched'])}")
    print(f"missing: {len(result['missing'])}")
    print(f"valid_labels: {len(result['valid_labels'])}")
    print(f"bad_labels: {len(result['bad_labels'])}")

    if result["missing"]:
        print("missing images:")
        print(*result["missing"], sep="\n")
    if result["bad_labels"]:
        print("invalid labels:")
        for filename, reason in result["bad_labels"].items():
            print(f"{filename}: {reason}")

    return 0 if not result["missing"] and not result["bad_labels"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
