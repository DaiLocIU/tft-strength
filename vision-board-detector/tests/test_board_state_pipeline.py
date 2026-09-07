import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from board_detector.board_state_pipeline import (  # noqa: E402
    combine_predictions,
    create_board_state,
)


class BoardStatePipelineTest(unittest.TestCase):
    def test_asset_identity_alias_is_returned_as_the_player_facing_champion_name(self) -> None:
        combined = combine_predictions(
            [
                {
                    "row": 3,
                    "column": 2,
                    "class_name": "occupied",
                    "confidence": 0.91,
                    "occupied": True,
                }
            ],
            {(3, 2): 0.84},
            {(3, 2): "ancient_sentinel"},
            {(3, 2): 0.92},
            {
                (3, 2): [
                    {"champion_name": "ancient_sentinel", "confidence": 0.92}
                ]
            },
            {(3, 2): "1star"},
            {(3, 2): 0.91},
            {(3, 2): [{"star_label": "1star", "confidence": 0.91}]},
            set(),
            0.75,
        )

        board_state = create_board_state(
            "image_388.png",
            combined,
            {
                "champion_confidence": 0.5,
                "identity_padding_ratio": 0.08,
                "identity_confidence_threshold": 0.75,
            },
        )

        unit = board_state["units"][0]
        self.assertEqual(unit["champion"], "Sentinel")
        self.assertEqual(unit["raw_champion"], "ancient_sentinel")
        self.assertEqual(unit["identity_candidates"][0]["champion_name"], "Sentinel")

    def test_low_identity_confidence_keeps_raw_candidate_but_returns_unknown(self) -> None:
        combined = combine_predictions(
            [
                {
                    "row": 3,
                    "column": 2,
                    "class_name": "occupied",
                    "confidence": 0.91,
                    "occupied": True,
                }
            ],
            {(3, 2): 0.84},
            {(3, 2): "alune"},
            {(3, 2): 0.34},
            {(3, 2): [{"champion_name": "alune", "confidence": 0.34}]},
            {(3, 2): "2star"},
            {(3, 2): 0.91},
            {(3, 2): [{"star_label": "2star", "confidence": 0.91}]},
            set(),
            0.75,
        )

        board_state = create_board_state(
            "image_388.png",
            combined,
            {
                "champion_confidence": 0.5,
                "identity_padding_ratio": 0.08,
                "identity_confidence_threshold": 0.75,
            },
        )

        self.assertEqual(combined[0]["source"], "both")
        self.assertEqual(board_state["units"][0]["champion"], "unknown")
        self.assertEqual(board_state["units"][0]["raw_champion"], "alune")
        self.assertEqual(board_state["units"][0]["star"], "2star")
        self.assertEqual(board_state["units"][0]["star_confidence"], 0.91)
        self.assertTrue(board_state["units"][0]["needs_review"])
        self.assertEqual(len(board_state["review"]["low_identity_confidence"]), 1)

    def test_occupancy_only_hex_is_reported_as_missing_hex(self) -> None:
        combined = combine_predictions(
            [
                {
                    "row": 2,
                    "column": 5,
                    "class_name": "occupied",
                    "confidence": 0.96,
                    "occupied": True,
                }
            ],
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            set(),
            0.75,
        )

        board_state = create_board_state(
            "image_388.png",
            combined,
            {
                "champion_confidence": 0.5,
                "identity_padding_ratio": 0.08,
                "identity_confidence_threshold": 0.75,
            },
        )

        self.assertEqual(board_state["units"][0]["champion"], "unknown")
        self.assertEqual(board_state["units"][0]["star"], "unknown")
        self.assertEqual(board_state["review"]["missing_hexes"][0]["row"], 2)
        self.assertEqual(board_state["review"]["missing_hexes"][0]["column"], 5)


if __name__ == "__main__":
    unittest.main()
