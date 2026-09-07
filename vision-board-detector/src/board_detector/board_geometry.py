from math import cos, pi, sin
from pathlib import Path
from typing import TypedDict

from PIL import Image


class HexCell(TypedDict):
    row: int
    column: int
    center_x: float
    center_y: float
    radius: float


class HexTuning(TypedDict):
    width_percent: float
    height_percent: float
    radius_percent: float
    gap_percent: float
    image_name: str


DEFAULT_TUNING: HexTuning = {
    "width_percent": 13.5,
    "height_percent": 90.0,
    "radius_percent": 5.4,
    "gap_percent": 3.7,
    "image_name": "image_1.png",
}
ROW_RADIUS_SCALE = {
    3: 1.0,
    2: 1.0,
    1: 1.0,
    0: 1.0,
}
ROW_RIGHT_SHIFT_SCALE = {
    3: 0.0,
    2: 0.06,
    1: 0.18,
    0: 0.32,
}
ROW_GAP_SCALE = {
    3: 1.0,
    2: 0.88,
    1: 0.76,
    0: 0.64,
}
HEX_DRAW_WIDTH_SCALE = 1.15
HEX_DRAW_HEIGHT_SCALE_BY_ROW = {
    3: 0.98,
    2: 0.93,
    1: 0.89,
    0: 0.82,
}
PATCH_SIZE_SCALE = 2.2
PATCH_UP_SHIFT_SCALE = 0.35


def make_tuning_for_image(image_name: str) -> HexTuning:
    return {
        "width_percent": DEFAULT_TUNING["width_percent"],
        "height_percent": DEFAULT_TUNING["height_percent"],
        "radius_percent": DEFAULT_TUNING["radius_percent"],
        "gap_percent": DEFAULT_TUNING["gap_percent"],
        "image_name": image_name,
    }


def create_bottom_left_hex_cell(
    image_path: str,
    width_percent: float,
    height_percent: float,
    radius_percent: float,
) -> HexCell:
    image = Image.open(image_path)
    width = image.width
    height = image.height

    return {
        "row": 3,
        "column": 0,
        "center_x": width * (width_percent / 100),
        "center_y": height * (height_percent / 100),
        "radius": width * (radius_percent / 100),
    }


def create_board_hex_cells_for_size(
    width: int,
    height: int,
    tuning: HexTuning,
) -> list[HexCell]:
    bottom_start_x = width * (tuning["width_percent"] / 100)
    bottom_center_y = height * (tuning["height_percent"] / 100)
    bottom_radius = width * (tuning["radius_percent"] / 100)
    vertical_step = 1.5 * bottom_radius
    hexes: list[HexCell] = []

    for row in [3, 2, 1, 0]:
        radius = bottom_radius * ROW_RADIUS_SCALE[row]
        border_gap = width * (tuning["gap_percent"] / 100) * ROW_GAP_SCALE[row]
        hex_width = 2 * radius * cos(pi / 6)
        center_step = hex_width + border_gap
        stagger_offset = -center_step / 2 if row in {2, 0} else 0.0
        right_shift = center_step * ROW_RIGHT_SHIFT_SCALE[row]
        row_from_bottom = 3 - row
        center_y = bottom_center_y - row_from_bottom * vertical_step

        for column in range(7):
            center_x = bottom_start_x + stagger_offset + right_shift + column * center_step
            hexes.append(
                {
                    "row": row,
                    "column": column,
                    "center_x": center_x,
                    "center_y": center_y,
                    "radius": radius,
                }
            )

    return hexes


def create_board_hex_cells(
    image_path: str,
    tuning: HexTuning,
) -> list[HexCell]:
    image = Image.open(image_path)
    return create_board_hex_cells_for_size(image.width, image.height, tuning)


def create_hex_polygon(hex_cell: HexCell) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    height_scale = HEX_DRAW_HEIGHT_SCALE_BY_ROW.get(hex_cell["row"], 1.0)

    for index in range(6):
        angle = pi / 6 + index * pi / 3
        x = hex_cell["center_x"] + hex_cell["radius"] * HEX_DRAW_WIDTH_SCALE * cos(angle)
        y = hex_cell["center_y"] + hex_cell["radius"] * height_scale * sin(angle)
        points.append((x, y))

    return points


def crop_hex_patch(image: Image.Image, hex_cell: HexCell) -> Image.Image:
    patch_size = int(hex_cell["radius"] * PATCH_SIZE_SCALE)
    patch_size = max(patch_size, 32)
    half_size = patch_size / 2

    crop_center_x = hex_cell["center_x"]
    crop_center_y = hex_cell["center_y"] - hex_cell["radius"] * PATCH_UP_SHIFT_SCALE

    left = int(round(crop_center_x - half_size))
    top = int(round(crop_center_y - half_size))
    right = left + patch_size
    bottom = top + patch_size

    source_left = max(left, 0)
    source_top = max(top, 0)
    source_right = min(right, image.width)
    source_bottom = min(bottom, image.height)

    patch = Image.new("RGB", (patch_size, patch_size), "black")
    source_crop = image.crop((source_left, source_top, source_right, source_bottom))
    paste_x = source_left - left
    paste_y = source_top - top
    patch.paste(source_crop, (paste_x, paste_y))

    return patch


def cell_id(hex_cell: HexCell) -> str:
    return f"{hex_cell['row']},{hex_cell['column']}"


def polygon_points_for_svg(hex_cell: HexCell) -> str:
    points = create_hex_polygon(hex_cell)
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def patch_file_name(image_name: str, hex_cell: HexCell) -> str:
    image_stem = Path(image_name).stem
    return f"{image_stem}_r{hex_cell['row']}_c{hex_cell['column']}.png"


def find_hex_cell(hexes: list[HexCell], row: int, column: int) -> HexCell:
    for hex_cell in hexes:
        if hex_cell["row"] == row and hex_cell["column"] == column:
            return hex_cell

    raise ValueError(f"Hex not found: {row},{column}")
