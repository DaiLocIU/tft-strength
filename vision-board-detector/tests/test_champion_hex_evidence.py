import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PIL import Image  # noqa: E402

from board_detector.champion_hex_evidence import (  # noqa: E402
    crop_champion_box,
    crop_champion_star_box,
    find_best_hex_for_champion_box,
)
from board_detector.model_adapters import ChampionBox  # noqa: E402


class ChampionHexEvidenceTest(unittest.TestCase):
    def test_large_box_chooses_one_occupied_hex_near_foot_point(self) -> None:
        box: ChampionBox = {
            "x1": 0,
            "y1": 0,
            "x2": 120,
            "y2": 200,
            "confidence": 0.9,
        }
        top_hex = {
            "row": 1,
            "column": 4,
            "center_x": 60,
            "center_y": 70,
            "radius": 20,
        }
        bottom_hex = {
            "row": 3,
            "column": 4,
            "center_x": 60,
            "center_y": 190,
            "radius": 20,
        }

        chosen_hex, occupied_candidates, point = find_best_hex_for_champion_box(
            box,
            [top_hex, bottom_hex],
            {(1, 4), (3, 4)},
            240,
            0.0,
        )

        self.assertEqual(chosen_hex["row"], 3)
        self.assertEqual(chosen_hex["column"], 4)
        self.assertEqual([hex_cell["row"] for hex_cell in occupied_candidates], [1, 3])
        self.assertEqual(point, (60, 200))

    def test_crop_champion_box_applies_padding_and_clamps_to_image(self) -> None:
        image = Image.new("RGB", (100, 100))
        box: ChampionBox = {
            "x1": 5,
            "y1": 10,
            "x2": 45,
            "y2": 60,
            "confidence": 0.8,
        }

        crop = crop_champion_box(image, box, 0.1)

        self.assertEqual(crop.size, (48, 60))

    def test_crop_champion_star_box_uses_asymmetric_padding(self) -> None:
        image = Image.new("RGB", (200, 200))
        box: ChampionBox = {
            "x1": 50,
            "y1": 60,
            "x2": 150,
            "y2": 160,
            "confidence": 0.8,
        }

        crop = crop_champion_star_box(image, box)

        self.assertEqual(crop.size, (153, 165))


if __name__ == "__main__":
    unittest.main()
