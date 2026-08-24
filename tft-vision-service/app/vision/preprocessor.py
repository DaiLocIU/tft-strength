import io
import cv2
import numpy as np
from PIL import Image


def load_image(image_input) -> np.ndarray:
    """Load image from file path, bytes, or numpy array into BGR format."""
    if isinstance(image_input, np.ndarray):
        return image_input

    if isinstance(image_input, (bytes, bytearray)):
        nparr = np.frombuffer(image_input, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    elif isinstance(image_input, str):
        img = cv2.imread(image_input, cv2.IMREAD_UNCHANGED)
    else:
        raise ValueError(f"Unsupported image input type: {type(image_input)}")

    if img is None:
        raise ValueError("Failed to decode image.")

    # Convert 4-channel RGBA to 3-channel BGR if alpha present
    if len(img.shape) == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    return img


def to_grayscale(img: np.ndarray) -> np.ndarray:
    """Convert BGR image to grayscale."""
    if len(img.shape) == 2:
        return img
    if len(img.shape) == 3 and img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def resize_image(img: np.ndarray, target_width: int) -> np.ndarray:
    """Resize image maintaining aspect ratio."""
    h, w = img.shape[:2]
    if w == target_width:
        return img
    ratio = target_width / float(w)
    target_height = int(h * ratio)
    return cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_AREA)


def create_champion_mask(h: int, w: int, trim_healthbar_pct: float = 0.16) -> np.ndarray:
    """
    Creates an elliptical soft-focus mask that:
    1. Trims the upper health bar / star level area (top ~16%).
    2. Zeroes out the outer hex floor corners so only the core champion body is matched.
    """
    mask = np.zeros((h, w), dtype=np.uint8)
    center_x = w // 2
    # Shift center slightly lower to account for health bar trimming
    center_y = int(h * 0.58)
    radius_x = int(w * 0.44)
    radius_y = int(h * 0.40)

    # Draw filled ellipse covering champion body
    cv2.ellipse(mask, (center_x, center_y), (radius_x, radius_y), 0, 0, 360, 255, -1)

    # Hard-cut upper health bar region
    cut_top = int(h * trim_healthbar_pct)
    mask[:cut_top, :] = 0

    # Soften edges with slight Gaussian blur
    mask = cv2.GaussianBlur(mask, (7, 7), 2.0)
    return mask
