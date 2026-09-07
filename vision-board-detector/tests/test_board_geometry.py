import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from board_detector.board_geometry import (  # noqa: E402
    create_board_hex_cells_for_size,
    create_hex_polygon,
    find_hex_cell,
    make_tuning_for_image,
)


class BoardGeometryTest(unittest.TestCase):
    def test_hex_grid_has_four_rows_and_seven_columns(self) -> None:
        hexes = create_board_hex_cells_for_size(1000, 500, make_tuning_for_image("board.png"))

        self.assertEqual(len(hexes), 28)
        self.assertEqual(hexes[0]["row"], 3)
        self.assertEqual(hexes[0]["column"], 0)
        self.assertEqual(hexes[-1]["row"], 0)
        self.assertEqual(hexes[-1]["column"], 6)

    def test_cell_lookup_and_projected_polygon_are_stable(self) -> None:
        hexes = create_board_hex_cells_for_size(1000, 500, make_tuning_for_image("board.png"))
        hex_cell = find_hex_cell(hexes, 2, 3)
        polygon = create_hex_polygon(hex_cell)

        self.assertEqual(hex_cell["row"], 2)
        self.assertEqual(hex_cell["column"], 3)
        self.assertEqual(len(polygon), 6)
        self.assertGreater(max(x for x, _ in polygon), hex_cell["center_x"])
        self.assertLess(min(y for _, y in polygon), hex_cell["center_y"])


if __name__ == "__main__":
    unittest.main()
