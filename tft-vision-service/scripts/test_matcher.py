import glob
import os
import sys

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
from app.vision.matcher import TemplateMatcher
from app.vision.preprocessor import load_image
from app.vision.roi import ROIExtractor


def run_benchmark(
    screenshot_path: str = None,
    icons_dir: str = "data/reference_icons",
    output_path: str = "data/debug_detection.png",
    threshold: float = 0.58,
):
    matcher = TemplateMatcher(icons_dir=icons_dir)
    print(f"Loaded {len(matcher.templates)} champion reference icons from {icons_dir}")

    if not matcher.templates:
        print(
            f"No reference icons found in '{icons_dir}'. Please drop 10-15 champion .png icons into this directory first."
        )
        return

    if screenshot_path is None:
        screenshots = sorted(glob.glob("data/screenshots/*.png"))
        if not screenshots:
            print("No screenshots found in data/screenshots/")
            return
        screenshot_path = screenshots[0]

    print(f"Running detection on screenshot: {screenshot_path}")
    full_img = load_image(screenshot_path)

    # Extract field ROI (board + bench)
    field_roi, (offset_x, offset_y) = ROIExtractor.extract_roi(full_img, "field")

    detections = matcher.match(
        field_roi,
        threshold=threshold,
        scales=[0.85, 0.95, 1.0, 1.05, 1.15],
        x_offset=offset_x,
        y_offset=offset_y,
    )

    print(f"\nFound {len(detections)} champion detections:")
    debug_img = full_img.copy()

    # Draw ROI bounding box
    fh, fw = field_roi.shape[:2]
    cv2.rectangle(
        debug_img,
        (offset_x, offset_y),
        (offset_x + fw, offset_y + fh),
        (255, 150, 0),
        2,
    )

    for idx, d in enumerate(detections):
        x, y, w, h = d.bbox
        print(
            f" #{idx + 1}: {d.champion} (conf: {d.confidence * 100:.1f}%) at ({x}, {y})"
        )

        # Draw green bounding box for detections
        cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 3)

        # Draw label badge
        label = f"{d.champion} {d.confidence * 100:.0f}%"
        cv2.putText(
            debug_img,
            label,
            (x, max(30, y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    cv2.imwrite(output_path, debug_img)
    print(f"\nSaved debug visual with bounding boxes to: {output_path}")


if __name__ == "__main__":
    screen_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run_benchmark(screenshot_path=screen_arg)
