"""Conservative HUD OCR for desktop TFT screenshots. Never guesses missing values.

Tesseract 5 with English data must be installed separately. Coordinates are
normalized to the full screenshot, including modest browser/video borders.
"""

from __future__ import annotations

import csv
import io
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image

REGIONS = {
    "round": (0.397, 0.083, 0.424, 0.108),
    "level": (0.181, 0.79, 0.19, 0.815),
    "gold": (0.535, 0.79, 0.55, 0.815),
    "hp": (0.93, 0.18, 0.95, 0.83),
    "streak": (0.594, 0.787, 0.608, 0.813),
}


def missing(reason: str) -> dict[str, Any]:
    return {
        "value": None,
        "confidence": None,
        "source": "ocr",
        "needs_review": True,
        "reason": reason,
    }


def read_tokens(
    image: Image.Image, region: tuple[float, ...], executable: str
) -> list[dict[str, Any]]:
    width, height = image.size
    x, y, right, bottom = region
    crop = image.crop((int(x * width), int(y * height), int(right * width), int(bottom * height)))
    crop = crop.resize((crop.width * 2, crop.height * 2))
    buffer = io.BytesIO()
    crop.save(buffer, format="PNG")
    result = subprocess.run(
        [
            executable,
            "stdin",
            "stdout",
            "-l",
            "eng",
            "--psm",
            ("7" if region[3] - region[1] < 0.05 else "11"),
            "tsv",
        ],
        input=buffer.getvalue(),
        capture_output=True,
        timeout=12,
        check=True,
    )
    rows = csv.DictReader(
        io.StringIO(result.stdout.decode()), delimiter="\t", quoting=csv.QUOTE_NONE
    )
    return [
        dict(
            text=row["text"].strip(),
            confidence=float(row["conf"]) / 100,
            y=y + float(row["top"]) / (2 * height),
            height=float(row["height"]) / (2 * height),
        )
        for row in rows
        if row.get("text", "").strip() and float(row["conf"]) >= 0
    ]


def select_value(field: str, tokens: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = []
    for token in tokens:
        text = token["text"]
        if field == "round":
            if not re.fullmatch(r"[1-9]-[1-7]", text):
                continue
            value: Any = text
        else:
            if not re.fullmatch(r"\d{1,3}", text):
                continue
            value = int(text)
            low, high = {"level": (1, 11), "gold": (0, 999), "hp": (0, 100), "streak": (0, 99)}[
                field
            ]
            if not low <= value <= high:
                continue
        # Constrained digit OCR confidence is evidence, not calibrated accuracy.
        if token["confidence"] < 0.6:
            continue
        candidates.append({**token, "value": value})
    if field == "hp" and len(candidates) > 1:
        # The local player's expanded badge is larger than opponent HP labels.
        candidates.sort(key=lambda t: t["height"], reverse=True)
        if candidates[0]["height"] < candidates[1]["height"] * 1.35:
            return missing("Player HP badge is ambiguous; enter your HP manually.")
        candidates = candidates[:1]
    values = {c["value"] for c in candidates}
    if len(values) != 1:
        return missing("Not readable or multiple candidates; enter this field manually.")
    best = max(candidates, key=lambda t: t["confidence"])
    return {
        "value": best["value"],
        "confidence": round(best["confidence"], 3),
        "source": "ocr",
        "needs_review": True,
        "reason": "Check against the screenshot before confirming.",
    }


def streak_direction(image: Image.Image, region: tuple[float, ...]) -> int | None:
    x, y, right, bottom = region
    crop = image.crop(
        (
            int(x * image.width),
            int(y * image.height),
            int(right * image.width),
            int(bottom * image.height),
        )
    )
    pixels = list(crop.getdata())
    warm = sum(r > 65 and r > g * 1.3 and r > b * 1.5 for r, g, b in pixels)
    cool = sum(b > 65 and b > r * 1.5 and g > r * 1.25 for r, g, b in pixels)
    minimum = max(6, len(pixels) * 0.06)
    if warm >= minimum and warm > cool * 2:
        return 1
    if cool >= minimum and cool > warm * 2:
        return -1
    return None


def detect_hud(path: Path) -> dict[str, Any]:
    executable = shutil.which("tesseract")
    if not executable:
        return {
            field: missing("HUD OCR unavailable: install Tesseract with English language data.")
            for field in REGIONS
        }
    try:
        with Image.open(path) as source:
            image = source.convert("RGB")
        regions = dict(REGIONS)
        level_fallback = (0.203, 0.79, 0.215, 0.815)
        streak_icon = (0.579, 0.787, 0.590, 0.813)
        if image.width / image.height >= 1.7:
            regions["round"] = (0.395, 0.0, 0.42, 0.033)
            regions["level"] = (0.18, 0.81, 0.19, 0.85)
            regions["gold"] = (0.533, 0.815, 0.55, 0.842)
            regions["streak"] = (0.592, 0.803, 0.610, 0.838)
            level_fallback = (0.203, 0.81, 0.215, 0.85)
            streak_icon = (0.575, 0.809, 0.588, 0.836)
        results = {}
        for field, region in regions.items():
            try:
                results[field] = select_value(field, read_tokens(image, region, executable))
                if field == "level" and results[field]["value"] is None:
                    # English HUD puts the digit after "Lvl."; Korean HUD begins with it.
                    results[field] = select_value(
                        field, read_tokens(image, level_fallback, executable)
                    )
                if field == "streak" and results[field]["value"] is not None:
                    direction = streak_direction(image, streak_icon)
                    if results[field]["value"] == 0:
                        pass
                    elif direction is None:
                        results[field] = missing(
                            "Streak count or win/loss icon is unclear; "
                            "enter signed streak manually."
                        )
                    else:
                        results[field]["value"] *= direction
            except (subprocess.SubprocessError, OSError, ValueError, KeyError) as error:
                results[field] = missing(
                    f"Could not read HUD field ({type(error).__name__}). Enter it manually."
                )
        return results
    except (OSError, ValueError):
        return {field: missing("Original screenshot unavailable.") for field in REGIONS}
