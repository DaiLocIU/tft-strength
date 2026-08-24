import numpy as np
import pytest
from app.vision.matcher import Detection, TemplateMatcher, apply_nms
from app.vision.preprocessor import load_image, resize_image, to_grayscale
from app.vision.roi import ROIExtractor


def test_preprocessor():
    # 3-channel test image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    gray = to_grayscale(img)
    assert gray.shape == (100, 100)

    resized = resize_image(img, target_width=50)
    assert resized.shape[1] == 50
    assert resized.shape[0] == 50


def test_roi_extractor():
    img = np.zeros((1000, 1000, 3), dtype=np.uint8)
    cropped, (x, y) = ROIExtractor.extract_roi(img, "field")
    assert cropped.shape[0] > 0
    assert cropped.shape[1] > 0
    assert x > 0 and y > 0


def test_nms():
    # Two overlapping boxes for the same unit
    d1 = Detection(
        champion="jinx", confidence=0.92, bbox=(10, 10, 40, 40), center=(30, 30)
    )
    d2 = Detection(
        champion="jinx", confidence=0.85, bbox=(12, 12, 40, 40), center=(32, 32)
    )
    # Distinct non-overlapping box
    d3 = Detection(
        champion="vi", confidence=0.88, bbox=(200, 200, 40, 40), center=(220, 220)
    )

    filtered = apply_nms([d1, d2, d3], overlap_threshold=0.3)
    assert len(filtered) == 2
    assert filtered[0].champion == "jinx"
    assert filtered[0].confidence == 0.92
    assert filtered[1].champion == "vi"
