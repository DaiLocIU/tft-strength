import sys
import unittest
from pathlib import Path
from typing import Union

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PIL import Image  # noqa: E402

from board_detector.model_adapters import (  # noqa: E402
    classify_champion_star,
    classify_champion_identity,
    detect_board_box,
    detect_champion_boxes,
)


class FakeVector:
    def __init__(self, values: list[float]) -> None:
        self.values = values

    def __getitem__(self, index: int) -> float:
        return self.values[index]

    def argmax(self) -> int:
        return self.values.index(max(self.values))


class FakeBoxRow:
    def __init__(self, values: list[float]) -> None:
        self.values = values

    def tolist(self) -> list[float]:
        return self.values


class FakeBoxes:
    def __init__(self, rows: list[list[float]], confidences: list[float]) -> None:
        self.xyxy = [FakeBoxRow(row) for row in rows]
        self.conf = FakeVector(confidences)

    def __len__(self) -> int:
        return len(self.xyxy)


class FakeDetectionResult:
    def __init__(self, boxes: FakeBoxes) -> None:
        self.boxes = boxes


class FakeDetectionModel:
    def __init__(self, boxes: FakeBoxes) -> None:
        self.boxes = boxes
        self.calls: list[dict[str, object]] = []

    def __call__(self, source: object, **kwargs: object) -> list[FakeDetectionResult]:
        self.calls.append({"source": source, **kwargs})
        return [FakeDetectionResult(self.boxes)]


class FakeList:
    def __init__(self, values: list[Union[float, int]]) -> None:
        self.values = values

    def tolist(self) -> list[Union[float, int]]:
        return self.values


class FakeProbs:
    top1 = 1
    top1conf = 0.82
    top5 = FakeList([1, 0])
    top5conf = FakeList([0.82, 0.11])


class FakeClassificationResult:
    names = {0: "kayle", 1: "alune"}
    probs = FakeProbs()


class FakeClassificationModel:
    def __call__(self, source: object, **kwargs: object) -> list[FakeClassificationResult]:
        return [FakeClassificationResult()]


class ModelAdaptersTest(unittest.TestCase):
    def test_detect_board_box_returns_highest_confidence_box(self) -> None:
        model = FakeDetectionModel(
            FakeBoxes(
                [[10, 20, 30, 40], [50, 60, 70, 80]],
                [0.4, 0.9],
            )
        )

        detection = detect_board_box(Path("image.png"), model)  # type: ignore[arg-type]

        self.assertEqual(detection["x1"], 50)
        self.assertEqual(detection["confidence"], 0.9)

    def test_detect_champion_boxes_returns_all_boxes(self) -> None:
        model = FakeDetectionModel(
            FakeBoxes(
                [[1, 2, 3, 4], [5, 6, 7, 8]],
                [0.7, 0.8],
            )
        )

        boxes = detect_champion_boxes(Path("board.png"), model, 0.5)  # type: ignore[arg-type]

        self.assertEqual(len(boxes), 2)
        self.assertEqual(boxes[1]["x2"], 7)
        self.assertEqual(model.calls[0]["conf"], 0.5)

    def test_classify_champion_identity_returns_top_candidate_list(self) -> None:
        crop = Image.new("RGB", (32, 32))

        prediction = classify_champion_identity(
            crop,
            FakeClassificationModel(),  # type: ignore[arg-type]
            160,
        )

        self.assertEqual(prediction["champion_name"], "alune")
        self.assertEqual(prediction["confidence"], 0.82)
        self.assertEqual(prediction["candidates"][0]["champion_name"], "alune")

    def test_classify_champion_star_returns_top_candidate_list(self) -> None:
        crop = Image.new("RGB", (32, 32))

        prediction = classify_champion_star(
            crop,
            FakeClassificationModel(),  # type: ignore[arg-type]
            160,
        )

        self.assertEqual(prediction["star_label"], "alune")
        self.assertEqual(prediction["confidence"], 0.82)
        self.assertEqual(prediction["candidates"][0]["star_label"], "alune")


if __name__ == "__main__":
    unittest.main()
