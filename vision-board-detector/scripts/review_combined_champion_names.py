import argparse
import base64
import json
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from typing import Any, Optional, TypedDict
from urllib.parse import parse_qs, urlparse

import _bootstrap  # noqa: F401
from combine_hex_signals import (
    CHAMPION_CONFIDENCE,
    CHAMPION_IDENTITY_MODEL_PATH,
    CHAMPION_IDENTITY_PADDING_RATIO,
    CHAMPION_MODEL_PATH,
    CHAMPION_STAR_MODEL_PATH,
    CROPS_DIR,
)
from label_champion_identity import CHAMPION_NAMES, normalize_champion_name
from PIL import Image
from predict_hex_occupancy import MODEL_PATH as HEX_OCCUPANCY_MODEL_PATH
from predict_hex_occupancy import predict_board_hex_occupancy
from ultralytics import YOLO  # type: ignore[attr-defined]

from board_detector.board_geometry import create_board_hex_cells, make_tuning_for_image
from board_detector.champion_hex_evidence import (
    ChampionHexEvidence,
    classify_champion_crop,
    crop_champion_box,
    get_champion_hex_evidence,
    predict_champion_boxes,
)
from board_detector.model_adapters import ChampionBox

LABELED_DIR = Path("data/champion-identity/labeled")
REVIEW_JSON = Path("data/champion-identity/wrong-name-review.json")
DEFAULT_PORT = 8094

champion_model: Optional[YOLO] = None
identity_model: Optional[YOLO] = None
star_model: Optional[YOLO] = None
hex_occupancy_model: Optional[YOLO] = None


class SavedCorrection(TypedDict):
    image_name: str
    box_index: int
    previous_name: str
    corrected_name: str
    crop_path: str
    box: ChampionBox


def get_models() -> tuple[YOLO, YOLO, YOLO, YOLO]:
    global champion_model, hex_occupancy_model, identity_model, star_model

    if champion_model is None:
        champion_model = YOLO(CHAMPION_MODEL_PATH)

    if identity_model is None:
        identity_model = YOLO(CHAMPION_IDENTITY_MODEL_PATH)

    if star_model is None:
        star_model = YOLO(CHAMPION_STAR_MODEL_PATH)

    if hex_occupancy_model is None:
        hex_occupancy_model = YOLO(HEX_OCCUPANCY_MODEL_PATH)

    return champion_model, identity_model, star_model, hex_occupancy_model


def encode_image_as_data_uri(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def list_board_image_names() -> list[str]:
    return sorted(path.name for path in CROPS_DIR.glob("*.png"))


def choose_image_name(requested_name: Optional[str]) -> Optional[str]:
    image_names = list_board_image_names()

    if len(image_names) == 0:
        return None

    if requested_name in image_names:
        return requested_name

    return image_names[0]


def get_next_image_name(current_name: str) -> Optional[str]:
    image_names = list_board_image_names()

    if current_name not in image_names:
        return None

    next_index = image_names.index(current_name) + 1

    if next_index >= len(image_names):
        return None

    return image_names[next_index]


def read_corrections() -> dict[str, SavedCorrection]:
    if not REVIEW_JSON.exists():
        return {}

    return json.loads(REVIEW_JSON.read_text(encoding="utf-8"))


def write_corrections(corrections: dict[str, SavedCorrection]) -> None:
    REVIEW_JSON.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_JSON.write_text(json.dumps(corrections, indent=2, sort_keys=True), encoding="utf-8")


def correction_key(image_name: str, box_index: int) -> str:
    return f"{image_name}#{box_index}"


def crop_file_name(image_name: str, box_index: int, champion_name: str) -> str:
    image_stem = Path(image_name).stem
    normalized_name = normalize_champion_name(champion_name)
    return f"{image_stem}_box_{box_index:03d}_corrected_{normalized_name}.png"


def remove_previous_labeled_crop(file_name: str) -> None:
    if not LABELED_DIR.exists():
        return

    for class_dir in LABELED_DIR.iterdir():
        if not class_dir.is_dir():
            continue

        existing_path = class_dir / file_name

        if existing_path.exists():
            existing_path.unlink()


def get_champion_evidence_for_image(
    image_name: str,
    champion_confidence: float,
    identity_padding_ratio: float,
) -> list[ChampionHexEvidence]:
    board_crop_path = CROPS_DIR / image_name

    if not board_crop_path.exists():
        raise FileNotFoundError(f"Board crop not found: {board_crop_path}")

    (
        current_champion_model,
        current_identity_model,
        current_star_model,
        current_hex_occupancy_model,
    ) = get_models()
    hexes = sorted(
        create_board_hex_cells(str(board_crop_path), make_tuning_for_image(image_name)),
        key=lambda hex_cell: (hex_cell["row"], hex_cell["column"]),
    )
    occupancy_predictions = predict_board_hex_occupancy(
        board_crop_path,
        HEX_OCCUPANCY_MODEL_PATH,
        current_hex_occupancy_model,
    )
    evidence_summary = get_champion_hex_evidence(
        board_crop_path,
        current_champion_model,
        current_identity_model,
        current_star_model,
        champion_confidence,
        identity_padding_ratio,
        0.0,
        hexes,
        occupancy_predictions,
    )
    return evidence_summary["champion_evidence"]


def save_corrected_name(
    image_name: str,
    box_index: int,
    champion_name: str,
    champion_confidence: float,
    identity_padding_ratio: float,
) -> dict[str, Any]:
    normalized_name = normalize_champion_name(champion_name)
    board_crop_path = CROPS_DIR / image_name
    board_image = Image.open(board_crop_path).convert("RGB")
    current_champion_model, current_identity_model, _, _ = get_models()
    champion_boxes = predict_champion_boxes(
        board_crop_path,
        current_champion_model,
        champion_confidence,
    )

    if box_index < 0 or box_index >= len(champion_boxes):
        raise ValueError(f"Box index {box_index} not found for {image_name}")

    box = champion_boxes[box_index]
    crop = crop_champion_box(board_image, box, identity_padding_ratio)
    previous_prediction = classify_champion_crop(crop, current_identity_model)
    file_name = crop_file_name(image_name, box_index, normalized_name)
    output_dir = LABELED_DIR / normalized_name
    output_path = output_dir / file_name

    remove_previous_labeled_crop(file_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    crop.save(output_path)

    corrections = read_corrections()
    corrections[correction_key(image_name, box_index)] = {
        "image_name": image_name,
        "box_index": box_index,
        "previous_name": previous_prediction["champion_name"],
        "corrected_name": normalized_name,
        "crop_path": str(output_path),
        "box": box,
    }
    write_corrections(corrections)

    return {
        "champion": normalized_name,
        "saved": str(output_path),
    }


def render_page(
    image_name: str,
    champion_confidence: float,
    identity_padding_ratio: float,
) -> str:
    board_crop_path = CROPS_DIR / image_name
    image = Image.open(board_crop_path).convert("RGB")
    evidence = get_champion_evidence_for_image(
        image_name,
        champion_confidence,
        identity_padding_ratio,
    )
    corrections = read_corrections()
    image_names = list_board_image_names()
    image_index = image_names.index(image_name) + 1

    box_html_items: list[str] = []
    for index, item in enumerate(evidence):
        saved_class = " saved" if correction_key(image_name, index) in corrections else ""
        champion_name = escape(item["champion_name"])
        label = escape(
            f"{item['chosen_key'][0]},{item['chosen_key'][1]} "
            f"{item['champion_name']} - {item['identity_confidence']:.2f}"
        )
        box_html_items.append(
            f"""
          <g class="champion-box{saved_class}" data-box-index="{index}" data-name="{champion_name}">
            <rect
              x="{item["box"]["x1"]:.1f}"
              y="{item["box"]["y1"]:.1f}"
              width="{item["box"]["x2"] - item["box"]["x1"]:.1f}"
              height="{item["box"]["y2"] - item["box"]["y1"]:.1f}"
            />
            <text x="{item["box"]["x1"] + 6:.1f}" y="{max(20, item["box"]["y1"] - 8):.1f}">
              {label}
            </text>
          </g>
        """
        )

    box_html = "\n".join(box_html_items)
    options_html = "\n".join(
        f'<option value="{escape(name)}"{" selected" if name == image_name else ""}>'
        f"{escape(name)}</option>"
        for name in image_names
    )
    champion_options_html = "\n".join(
        f'<option value="{escape(name)}"></option>' for name in CHAMPION_NAMES
    )
    meta_text = (
        f"{escape(image_name)} - image {image_index} of {len(image_names)} - "
        f"{len(evidence)} boxes"
    )

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Combined Champion Name Review</title>
    <style>
      * {{
        box-sizing: border-box;
      }}

      body {{
        margin: 0;
        background: #f6f4ee;
        color: #172026;
        font-family:
          ui-sans-serif,
          system-ui,
          -apple-system,
          BlinkMacSystemFont,
          "Segoe UI",
          sans-serif;
      }}

      main {{
        max-width: 1400px;
        margin: 0 auto;
        padding: 20px;
      }}

      header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
        margin-bottom: 14px;
      }}

      h1 {{
        font-size: 24px;
        margin: 0;
      }}

      .meta {{
        color: #5f6c7b;
        font-size: 14px;
        margin: 4px 0 0;
      }}

      .toolbar {{
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
      }}

      select,
      input,
      button {{
        border: 1px solid #c7ccd1;
        border-radius: 6px;
        background: white;
        color: #172026;
        min-height: 38px;
        padding: 0 12px;
        font: inherit;
      }}

      select {{
        max-width: 260px;
      }}

      input {{
        width: 210px;
      }}

      button.primary {{
        background: #0f766e;
        border-color: #0f766e;
        color: white;
      }}

      .board {{
        position: relative;
        max-width: 100%;
        border: 1px solid #c7ccd1;
        border-radius: 8px;
        overflow: hidden;
        background: #111827;
      }}

      .board img {{
        display: block;
        width: 100%;
        height: auto;
      }}

      .overlay {{
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
      }}

      .champion-box rect {{
        fill: rgba(250, 204, 21, 0.12);
        stroke: #facc15;
        stroke-width: 4;
        cursor: pointer;
      }}

      .champion-box.saved rect {{
        fill: rgba(15, 118, 110, 0.22);
        stroke: #0f766e;
      }}

      .champion-box text {{
        fill: white;
        stroke: black;
        stroke-width: 5;
        paint-order: stroke;
        font-size: 23px;
        font-weight: 800;
        pointer-events: none;
      }}

      #status {{
        min-height: 22px;
        color: #0f766e;
        font-size: 14px;
        margin: 12px 0 0;
      }}

      .dialog-backdrop {{
        position: fixed;
        inset: 0;
        display: none;
        align-items: center;
        justify-content: center;
        background: rgba(15, 23, 42, 0.58);
        padding: 24px;
      }}

      .dialog-backdrop.open {{
        display: flex;
      }}

      .dialog {{
        width: min(440px, 100%);
        background: white;
        border: 1px solid #c7ccd1;
        border-radius: 8px;
        padding: 18px;
        box-shadow: 0 22px 60px rgba(15, 23, 42, 0.28);
      }}

      .dialog h2 {{
        font-size: 20px;
        margin: 0 0 12px;
      }}

      .dialog input {{
        width: 100%;
        margin-bottom: 14px;
      }}

      .dialog-actions {{
        display: flex;
        justify-content: flex-end;
        gap: 10px;
      }}
    </style>
  </head>
  <body>
    <main>
      <header>
        <div>
          <h1>Combined Champion Name Review</h1>
          <p class="meta">{meta_text}</p>
        </div>
        <div class="toolbar">
          <select id="imageSelect" aria-label="Choose image">
            {options_html}
          </select>
          <button class="primary" id="nextButton" type="button">Next image</button>
        </div>
      </header>

      <section class="board" aria-label="Champion names on board">
        <img src="{encode_image_as_data_uri(image)}" alt="{escape(image_name)}" />
        <svg class="overlay" viewBox="0 0 {image.width} {image.height}">
          {box_html}
        </svg>
      </section>

      <p id="status" aria-live="polite"></p>
    </main>

    <div class="dialog-backdrop" id="labelDialog" role="dialog" aria-modal="true">
      <div class="dialog">
        <h2 id="dialogTitle">Correct champion name</h2>
        <input
          id="dialogChampionInput"
          list="championNames"
          placeholder="search champion"
          autocomplete="off"
        />
        <datalist id="championNames">
          {champion_options_html}
        </datalist>
        <div class="dialog-actions">
          <button id="cancelButton" type="button">Cancel</button>
          <button class="primary" id="saveButton" type="button">Save correction</button>
        </div>
      </div>
    </div>

    <script>
      const imageName = {json.dumps(image_name)};
      const nextImageName = {json.dumps(get_next_image_name(image_name))};
      const championConfidence = {json.dumps(champion_confidence)};
      const identityPaddingRatio = {json.dumps(identity_padding_ratio)};
      const imageSelect = document.querySelector("#imageSelect");
      const nextButton = document.querySelector("#nextButton");
      const statusText = document.querySelector("#status");
      const labelDialog = document.querySelector("#labelDialog");
      const dialogTitle = document.querySelector("#dialogTitle");
      const dialogChampionInput = document.querySelector("#dialogChampionInput");
      const cancelButton = document.querySelector("#cancelButton");
      const saveButton = document.querySelector("#saveButton");
      let activeBoxGroup = null;

      function urlForImage(name) {{
        const params = new URLSearchParams();
        params.set("image", name);
        params.set("champion_conf", String(championConfidence));
        params.set("identity_padding", String(identityPaddingRatio));
        return "/?" + params.toString();
      }}

      function openLabelDialog(boxGroup) {{
        activeBoxGroup = boxGroup;
        dialogTitle.textContent = `Correct box ${{boxGroup.dataset.boxIndex}}`;
        dialogChampionInput.value = boxGroup.dataset.name || "";
        labelDialog.classList.add("open");
        dialogChampionInput.focus();
        dialogChampionInput.select();
      }}

      function closeLabelDialog() {{
        labelDialog.classList.remove("open");
        activeBoxGroup = null;
      }}

      async function saveCorrection() {{
        if (!activeBoxGroup) {{
          return;
        }}

        const championName = dialogChampionInput.value.trim();

        if (!championName) {{
          statusText.textContent = "Choose or type a champion name.";
          return;
        }}

        const response = await fetch("/save", {{
          method: "POST",
          headers: {{"Content-Type": "application/json"}},
          body: JSON.stringify({{
            image: imageName,
            box_index: Number(activeBoxGroup.dataset.boxIndex),
            champion: championName,
            champion_conf: championConfidence,
            identity_padding: identityPaddingRatio,
          }}),
        }});
        const result = await response.json();

        if (!response.ok) {{
          statusText.textContent = result.error || "Save failed.";
          return;
        }}

        activeBoxGroup.classList.add("saved");
        activeBoxGroup.dataset.name = result.champion;
        activeBoxGroup.querySelector("text").textContent = result.champion;
        statusText.textContent = `Saved correction: ${{result.champion}}`;
        closeLabelDialog();
      }}

      document.querySelectorAll(".champion-box").forEach((boxGroup) => {{
        boxGroup.addEventListener("click", () => openLabelDialog(boxGroup));
      }});

      cancelButton.addEventListener("click", closeLabelDialog);
      saveButton.addEventListener("click", saveCorrection);
      dialogChampionInput.addEventListener("keydown", (event) => {{
        if (event.key === "Enter") {{
          saveCorrection();
        }}

        if (event.key === "Escape") {{
          closeLabelDialog();
        }}
      }});
      labelDialog.addEventListener("click", (event) => {{
        if (event.target === labelDialog) {{
          closeLabelDialog();
        }}
      }});
      imageSelect.addEventListener("change", () => {{
        window.location.href = urlForImage(imageSelect.value);
      }});
      nextButton.addEventListener("click", () => {{
        if (!nextImageName) {{
          statusText.textContent = "No next image.";
          return;
        }}

        window.location.href = urlForImage(nextImageName);
      }});
    </script>
  </body>
</html>"""


class CombinedChampionNameReviewHandler(BaseHTTPRequestHandler):
    champion_confidence = CHAMPION_CONFIDENCE
    identity_padding_ratio = CHAMPION_IDENTITY_PADDING_RATIO

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)

        if parsed_url.path != "/":
            self.send_error(404)
            return

        query = parse_qs(parsed_url.query)
        requested_image = query.get("image", [None])[0]
        champion_confidence = float(
            query.get("champion_conf", [str(self.champion_confidence)])[0]
        )
        identity_padding_ratio = float(
            query.get("identity_padding", [str(self.identity_padding_ratio)])[0]
        )
        image_name = choose_image_name(requested_image)

        if image_name is None:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"No board crops found.")
            return

        try:
            page = render_page(image_name, champion_confidence, identity_padding_ratio)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))
        except Exception as error:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(str(error).encode("utf-8"))

    def do_POST(self) -> None:
        if self.path != "/save":
            self.send_error(404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body)
            result = save_corrected_name(
                str(payload["image"]),
                int(payload["box_index"]),
                str(payload["champion"]),
                float(payload.get("champion_conf", self.champion_confidence)),
                float(payload.get("identity_padding", self.identity_padding_ratio)),
            )
            self.send_response(200)
        except Exception as error:
            result = {"error": str(error)}
            self.send_response(400)

        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--champion-conf", type=float, default=CHAMPION_CONFIDENCE)
    parser.add_argument("--identity-padding", type=float, default=CHAMPION_IDENTITY_PADDING_RATIO)
    args = parser.parse_args()

    CombinedChampionNameReviewHandler.champion_confidence = args.champion_conf
    CombinedChampionNameReviewHandler.identity_padding_ratio = args.identity_padding
    server = ThreadingHTTPServer(("0.0.0.0", args.port), CombinedChampionNameReviewHandler)
    print(f"Combined champion name review running at http://localhost:{args.port}")
    print(f"Reading board crops from {CROPS_DIR}")
    print(f"Saving corrected crops to {LABELED_DIR}")
    print(f"Corrections recorded at {REVIEW_JSON}")
    server.serve_forever()


if __name__ == "__main__":
    main()
