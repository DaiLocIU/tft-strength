import os
import sys
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_DIR = os.path.join(PROJECT_ROOT, "data", "screenshots")
OUT_DIR = os.path.join(PROJECT_ROOT, "data", "reference_icons")

os.makedirs(OUT_DIR, exist_ok=True)

# Image 2 specific crops (ymin, xmin, ymax, xmax)
IMAGE_2_CROPS = {
    # --- Board Units ---
    "Elder_Dragon": (0.13, 0.41, 0.29, 0.53),
    "Scuttlecrab": (0.41, 0.28, 0.52, 0.35),
    "Gromp_Left": (0.41, 0.34, 0.52, 0.41),
    "Gromp_Center": (0.36, 0.38, 0.46, 0.45),
    "Elderwood_Woodnt": (0.36, 0.44, 0.47, 0.50),
    "Gromp_Right": (0.35, 0.50, 0.46, 0.57),
    "Cinderling": (0.38, 0.57, 0.46, 0.62),
    "Azir_Bird": (0.51, 0.40, 0.62, 0.46),
    "Faerie_Dragon": (0.51, 0.51, 0.58, 0.56),
    "Lucian_like_Unit": (0.53, 0.61, 0.63, 0.67),
    "Aatrox_Demonic": (0.53, 0.68, 0.66, 0.74),
    # --- Bench Units ---
    "Bench_Urgot_Summon": (0.54, 0.22, 0.64, 0.28),
    "Bench_Demon": (0.55, 0.27, 0.63, 0.34),
    "Bench_Assassin": (0.68, 0.19, 0.74, 0.25),
    # --- Shop Cards ---
    "Shop_Teemo": (0.82, 0.28, 0.95, 0.39),
    "Shop_Morgana": (0.82, 0.39, 0.95, 0.50),
    "Shop_Kayle": (0.82, 0.50, 0.95, 0.60),
    "Shop_Malphite": (0.82, 0.60, 0.95, 0.71),
    "Shop_Aphelios": (0.82, 0.71, 0.95, 0.81),
}


def crop_image(screenshot_filename: str, crops_dict: dict):
    image_path = os.path.join(SCREENSHOTS_DIR, screenshot_filename)
    if not os.path.exists(image_path):
        print(f"Error: Screenshot not found at {image_path}")
        return

    img = Image.open(image_path)
    width, height = img.size
    print(f"\n--- Processing {screenshot_filename} ({width}x{height}) ---")

    saved_count = 0
    for name, (ymin, xmin, ymax, xmax) in crops_dict.items():
        box = (
            int(xmin * width),
            int(ymin * height),
            int(xmax * width),
            int(ymax * height),
        )
        cropped_img = img.crop(box)
        filename = f"{name.lower()}.png"
        save_path = os.path.join(OUT_DIR, filename)
        cropped_img.save(save_path)
        saved_count += 1
        print(
            f"Saved: {filename} ({cropped_img.size[0]}x{cropped_img.size[1]} px)"
        )

    print(f"Saved {saved_count} reference icons to {OUT_DIR}")


if __name__ == "__main__":
    crop_image("image_2.png", IMAGE_2_CROPS)
