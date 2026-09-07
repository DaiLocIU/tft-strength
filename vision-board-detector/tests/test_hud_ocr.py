import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from PIL import Image

from board_detector.hud_ocr import detect_hud, select_value, streak_direction


def token(text, confidence=0.95, height=0.02):
    return dict(text=text, confidence=confidence, height=height, y=0.5)


class HudOcrTest(unittest.TestCase):
    def test_round_requires_valid_stage_and_round(self):
        self.assertEqual(select_value("round", [token("2-1")])["value"], "2-1")
        for value in ["2-9", "0-1", "21", "10:30"]:
            self.assertIsNone(select_value("round", [token(value)])["value"])

    def test_zero_gold_and_hp_are_real_values(self):
        for field in ["gold", "hp"]:
            self.assertEqual(select_value(field, [token("0")])["value"], 0)

    def test_abstains_for_ambiguous_and_low_confidence_text(self):
        self.assertIsNone(select_value("gold", [token("7"), token("8")])["value"])
        self.assertIsNone(select_value("level", [token("4", 0.2)])["value"])
        self.assertIsNone(select_value("hp", [token("101")])["value"])

    def test_does_not_select_opponent_hp_when_badges_are_same_size(self):
        self.assertIsNone(select_value("hp", [token("90"), token("80")])["value"])

    def test_streak_direction_requires_a_distinct_icon_color(self):
        self.assertEqual(
            streak_direction(Image.new("RGB", (20, 20), (200, 100, 20)), (0, 0, 1, 1)), 1
        )
        self.assertEqual(
            streak_direction(Image.new("RGB", (20, 20), (20, 150, 210)), (0, 0, 1, 1)), -1
        )
        self.assertIsNone(
            streak_direction(Image.new("RGB", (20, 20), (100, 100, 100)), (0, 0, 1, 1))
        )

    def test_missing_ocr_does_not_fail_board_detection(self):
        with patch("board_detector.hud_ocr.shutil.which", return_value=None):
            hud = detect_hud(Path("missing.png"))
        self.assertEqual(set(hud), {"round", "level", "gold", "hp", "streak"})
        self.assertTrue(all(field["value"] is None for field in hud.values()))


if __name__ == "__main__":
    unittest.main()
