from typing import Dict, Tuple
import numpy as np


class ROIExtractor:
    """Extracts Regions of Interest (ROI) from TFT screenshots based on resolution proportions."""

    # Proportional bounding boxes (y_min_ratio, y_max_ratio, x_min_ratio, x_max_ratio)
    # Calibrated for standard 16:10 / 16:9 full-screen TFT layouts
    REGIONS: Dict[str, Tuple[float, float, float, float]] = {
        # Active combat hex board area (avoiding HUD, traits sidebar, and top stage bar)
        "board": (0.20, 0.75, 0.15, 0.85),
        # Player bench slots (just below board grid)
        "bench": (0.70, 0.84, 0.16, 0.84),
        # Combined player field (board + bench)
        "field": (0.20, 0.84, 0.15, 0.85),
        # Shop card area at the bottom
        "shop": (0.83, 0.99, 0.22, 0.78),
    }

    @classmethod
    def extract_roi(
        cls, img: np.ndarray, region_name: str = "field"
    ) -> Tuple[np.ndarray, Tuple[int, int]]:
        """
        Extract specified region from image.
        Returns (cropped_image, (x_offset, y_offset)).
        """
        if region_name not in cls.REGIONS:
            raise ValueError(
                f"Unknown region '{region_name}'. Available: {list(cls.REGIONS.keys())}"
            )

        y_min_r, y_max_r, x_min_r, x_max_r = cls.REGIONS[region_name]
        h, w = img.shape[:2]

        ymin = int(h * y_min_r)
        ymax = int(h * y_max_r)
        xmin = int(w * x_min_r)
        xmax = int(w * x_max_r)

        cropped = img[ymin:ymax, xmin:xmax]
        return cropped, (xmin, ymin)
