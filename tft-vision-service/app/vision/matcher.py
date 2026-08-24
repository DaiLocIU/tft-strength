from dataclasses import dataclass
import glob
import os
from typing import List, Optional, Tuple
import cv2
import numpy as np

from app.vision.preprocessor import create_champion_mask, load_image, to_grayscale


@dataclass
class Detection:
    champion: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    center: Tuple[int, int]  # (center_x, center_y)


def apply_nms(
    detections: List[Detection], overlap_threshold: float = 0.30
) -> List[Detection]:
    """Non-Maximum Suppression to remove overlapping bounding box duplicates."""
    if not detections:
        return []

    # Sort detections by confidence descending
    sorted_dets = sorted(detections, key=lambda d: d.confidence, reverse=True)
    kept: List[Detection] = []

    for current in sorted_dets:
        discard = False
        cx, cy, cw, ch = current.bbox
        current_box = [cx, cy, cx + cw, cy + ch]
        current_area = cw * ch

        for existing in kept:
            ex, ey, ew, eh = existing.bbox
            existing_box = [ex, ey, ex + ew, ey + eh]
            existing_area = ew * eh

            # Compute Intersection over Union (IoU)
            ix1 = max(current_box[0], existing_box[0])
            iy1 = max(current_box[1], existing_box[1])
            ix2 = min(current_box[2], existing_box[2])
            iy2 = min(current_box[3], existing_box[3])

            iw = max(0, ix2 - ix1)
            ih = max(0, iy2 - iy1)
            intersection = iw * ih

            union = current_area + existing_area - intersection
            iou = intersection / float(union) if union > 0 else 0.0

            # Discard if overlapping heavily with a higher-scoring box
            if iou > overlap_threshold:
                discard = True
                break

        if not discard:
            kept.append(current)

    return kept


class TemplateMatcher:
    """
    High-precision multi-scale template matcher with:
    1. Elliptical noise masking (filters floor hex grid clutter).
    2. Health-bar & star-level region suppression.
    3. Row-adaptive perspective scaling.
    """

    def __init__(self, icons_dir: str = "data/reference_icons"):
        self.icons_dir = icons_dir
        self.templates: List[Tuple[str, np.ndarray, np.ndarray]] = []
        self.load_templates()

    def load_templates(self):
        """Loads all .png templates and pre-computes their champion masks."""
        self.templates = []
        pattern = os.path.join(self.icons_dir, "*.png")
        for filepath in sorted(glob.glob(pattern)):
            filename = os.path.splitext(os.path.basename(filepath))[0].lower()
            for suffix in ["_board", "_shop", "_icon", "_unit", "_left", "_right", "_center", "_bench"]:
                if suffix in filename:
                    filename = filename.replace(suffix, "")
                    break
            img = load_image(filepath)
            gray = to_grayscale(img)
            th, tw = gray.shape[:2]
            mask = create_champion_mask(th, tw)
            self.templates.append((filename, gray, mask))

    def match(
        self,
        target_image: np.ndarray,
        threshold: float = 0.58,
        scales: Optional[List[float]] = None,
        x_offset: int = 0,
        y_offset: int = 0,
    ) -> List[Detection]:
        """
        Runs masked multi-scale template matching across all loaded champion templates.
        """
        if not self.templates:
            return []

        target_gray = to_grayscale(target_image)
        h_target, w_target = target_gray.shape[:2]

        # Perspective row scales: 0.65x for back rows, up to 1.30x for front rows
        scales = scales or [0.65, 0.75, 0.85, 0.95, 1.0, 1.10, 1.20, 1.30]

        raw_detections: List[Detection] = []

        for champ_name, template, mask in self.templates:
            th, tw = template.shape[:2]

            for scale in scales:
                sw, sh = int(tw * scale), int(th * scale)
                if (
                    sw <= 0
                    or sh <= 0
                    or sh >= h_target
                    or sw >= w_target
                ):
                    continue

                scaled_template = cv2.resize(
                    template, (sw, sh), interpolation=cv2.INTER_AREA
                )
                scaled_mask = cv2.resize(
                    mask, (sw, sh), interpolation=cv2.INTER_AREA
                )

                try:
                    # Match with mask to suppress outer hex floor and health bar noise
                    res = cv2.matchTemplate(
                        target_gray, scaled_template, cv2.TM_CCORR_NORMED, mask=scaled_mask
                    )
                except cv2.error:
                    # Fallback to standard TM_CCOEFF_NORMED if mask fails on certain builds
                    res = cv2.matchTemplate(
                        target_gray, scaled_template, cv2.TM_CCOEFF_NORMED
                    )

                locs = np.where(res >= threshold)

                for pt in zip(*locs[::-1]):
                    score = float(res[pt[1], pt[0]])
                    gx = pt[0] + x_offset
                    gy = pt[1] + y_offset
                    cx = gx + sw // 2
                    cy = gy + sh // 2

                    raw_detections.append(
                        Detection(
                            champion=champ_name,
                            confidence=round(score, 3),
                            bbox=(gx, gy, sw, sh),
                            center=(cx, cy),
                        )
                    )

        return apply_nms(raw_detections, overlap_threshold=0.30)
