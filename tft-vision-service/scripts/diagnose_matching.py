import sys
import os

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from app.vision.matcher import TemplateMatcher
from app.vision.preprocessor import load_image, to_grayscale
from app.vision.roi import ROIExtractor


def diagnose_image(image_path: str):
    print(f"\n==================================================")
    print(f"DIAGNOSING: {image_path}")
    print(f"==================================================")

    matcher = TemplateMatcher("data/reference_icons")
    full_img = load_image(image_path)
    field_roi, (ox, oy) = ROIExtractor.extract_roi(full_img, "field")
    gray_roi = to_grayscale(field_roi)

    print(f"Target ROI size: {gray_roi.shape[1]}x{gray_roi.shape[0]}")
    print(f"Loaded {len(matcher.templates)} templates.")

    # Test wider scales from 0.6x to 1.4x
    scales = [0.65, 0.75, 0.85, 0.95, 1.0, 1.05, 1.15, 1.25, 1.35]

    top_matches = []
    for name, tmpl in matcher.templates:
        best_score = -1.0
        best_scale = 1.0
        best_loc = (0, 0)
        best_size = (tmpl.shape[1], tmpl.shape[0])

        for scale in scales:
            sw = int(tmpl.shape[1] * scale)
            sh = int(tmpl.shape[0] * scale)
            if (
                sw <= 10
                or sh <= 10
                or sw >= gray_roi.shape[1]
                or sh >= gray_roi.shape[0]
            ):
                continue

            scaled_tmpl = cv2.resize(
                tmpl, (sw, sh), interpolation=cv2.INTER_AREA
            )
            res = cv2.matchTemplate(
                gray_roi, scaled_tmpl, cv2.TM_CCOEFF_NORMED
            )
            min_v, max_v, min_l, max_l = cv2.minMaxLoc(res)

            if max_v > best_score:
                best_score = float(max_v)
                best_scale = scale
                best_loc = max_l
                best_size = (sw, sh)

        top_matches.append((best_score, name, best_scale, best_loc, best_size))

    # Sort descending
    top_matches.sort(reverse=True, key=lambda x: x[0])

    print("\nTop 12 highest confidence template matches:")
    for score, name, scale, (x, y), (w, h) in top_matches[:12]:
        gx = x + ox
        gy = y + oy
        print(
            f" - {name:20s}: Score = {score*100:5.1f}% | Scale = {scale:.2f}x | Pos = ({gx}, {gy})"
        )


if __name__ == "__main__":
    target = (
        sys.argv[1] if len(sys.argv) > 1 else "data/screenshots/image_3.png"
    )
    diagnose_image(target)
