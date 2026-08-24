from dataclasses import dataclass
from typing import List, Tuple
import cv2
import numpy as np
from PIL import Image

from app.vision.classifier import ChampionClassifier, get_classifier
from app.vision.matcher import Detection, apply_nms


class HybridChampionDetector:
    """
    Combines spatial multi-scale candidate proposals with deep MobileNetV2
    feature embeddings for robust, invariant TFT unit detection.
    """

    def __init__(self, icons_dir: str = "data/reference_icons"):
        self.classifier = get_classifier(icons_dir=icons_dir)

    def detect_in_roi(
        self,
        full_image: np.ndarray,
        roi_bbox: Tuple[int, int, int, int],  # (x, y, w, h)
        threshold: float = 0.55,
        window_sizes: List[Tuple[int, int]] = None,
        stride: int = 50,
    ) -> List[Detection]:
        """
        Scans an ROI region using sliding window proposals classified by CNN embeddings.
        """
        rx, ry, rw, rh = roi_bbox
        roi_img = full_image[ry:ry + rh, rx:rx + rw]
        h_roi, w_roi = roi_img.shape[:2]

        if window_sizes is None:
            # Typical unit sizes at 3456x2234 resolution
            window_sizes = [
                (180, 200),
                (220, 250),
                (260, 300),
            ]

        candidates: List[Detection] = []

        # Convert ROI to PIL image for efficient cropping and PyTorch transforms
        if len(roi_img.shape) == 3 and roi_img.shape[2] == 4:
            roi_rgb = cv2.cvtColor(roi_img, cv2.COLOR_BGRA2RGB)
        elif len(roi_img.shape) == 3 and roi_img.shape[2] == 3:
            roi_rgb = cv2.cvtColor(roi_img, cv2.COLOR_BGR2RGB)
        else:
            roi_rgb = cv2.cvtColor(roi_img, cv2.COLOR_GRAY2RGB)

        pil_roi = Image.fromarray(roi_rgb)

        for win_w, win_h in window_sizes:
            if win_w >= w_roi or win_h >= h_roi:
                continue

            for y in range(0, h_roi - win_h, stride):
                for x in range(0, w_roi - win_w, stride):
                    crop = pil_roi.crop((x, y, x + win_w, y + win_h))
                    champ_name, conf = self.classifier.predict(crop)

                    if conf >= threshold and champ_name != "unknown":
                        gx = rx + x
                        gy = ry + y
                        cx = gx + win_w // 2
                        cy = gy + win_h // 2

                        candidates.append(
                            Detection(
                                champion=champ_name,
                                confidence=conf,
                                bbox=(gx, gy, win_w, win_h),
                                center=(cx, cy),
                            )
                        )

        # Apply Non-Maximum Suppression to eliminate overlapping window proposals
        return apply_nms(candidates, overlap_threshold=0.30)
