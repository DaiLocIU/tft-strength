import argparse
import base64
import json
import shutil
import zipfile
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from typing import Any, Optional, TypedDict
from urllib.parse import parse_qs, urlparse

from PIL import Image


EXPORT_ZIP = Path("exports/label-studio/champion-94.zip")
DATASET_DIR = Path("data/champion-identity")
SOURCE_DIR = DATASET_DIR / "source" / "champion-94"
LABELED_DIR = DATASET_DIR / "labeled"
LABELS_JSON = DATASET_DIR / "identity-labels.json"
DEFAULT_PORT = 8092
BOX_PADDING_RATIO = 0.08
START_IMAGE_INDEX: Optional[int] = None
END_IMAGE_INDEX: Optional[int] = None
CHAMPION_NAMES = [
    "Vi",
    "Morgana",
    "Maokai",
    "Alune",
    "Yunara",
    "LeBlanc",
    "Lifebloom",
    "Sivir",
    "Rengar",
    "Karma",
    "Zyra",
    "Ahri",
    "Ezreal",
    "The Elder Dragon",
    "Ivern",
    "Draven",
    "Lux (Solar)",
    "Lux (Primal)",
    "Lux (Lunar)",
    "Lux (Inferno)",
    "Lux (Fae)",
    "Lux (Elderwood)",
    "Lux (Coven)",
    "Lux (Blossom)",
    "Lux (Blackthorn)",
    "Taric",
    "Kennen",
    "Gnar",
    "Ashe",
    "Soraka",
    "Sett",
    "Ancient Sentinel",
    "Nidalee",
    "Malphite",
    "Lillia",
    "Brambleback",
    "Aphelios",
    "Amumu",
    "Tristana",
    "Rammus",
    "Master Yi",
    "Mama Beak",
    "Krug",
    "Kog'Maw",
    "Kha'Zix",
    "Hecarim",
    "Fiddlesticks",
    "Diana",
    "Cassiopeia",
    "Azir",
    "Warwick",
    "Teemo",
    "Shen",
    "Sejuani",
    "Stonebark Tree",
    "Training Dummy",
    "Scuttlecrab",
    "Murkwolf",
    "Kayle",
    "Gromp",
    "Elise",
    "Caitlyn",
    "Alistar",
    "Yorick",
    "Xayah",
    "Veigar",
    "Varus",
    "Rek'Sai",
    "Rakan",
    "Pebbles",
    "Ornn",
    "Leona",
    "Kobuko",
    "Cinderling",
    "Camille",
    "Akali",
    "Unknown",
]


class ChampionBox(TypedDict):
    index: int
    x1: float
    y1: float
    x2: float
    y2: float


def ensure_source_export_extracted() -> None:
    if (SOURCE_DIR / "images").exists() and (SOURCE_DIR / "labels").exists():
        return

    if not EXPORT_ZIP.exists():
        raise FileNotFoundError(f"Export zip not found: {EXPORT_ZIP}")

    if SOURCE_DIR.exists():
        shutil.rmtree(SOURCE_DIR)

    SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(EXPORT_ZIP) as archive:
        archive.extractall(SOURCE_DIR)


def image_index_from_name(image_name: str) -> Optional[int]:
    stem = Path(image_name).stem
    marker = "image_"
    marker_index = stem.rfind(marker)

    if marker_index == -1:
        return None

    index_text = stem[marker_index + len(marker) :]

    if not index_text.isdigit():
        return None

    return int(index_text)


def image_is_in_selected_range(image_name: str) -> bool:
    image_index = image_index_from_name(image_name)

    if image_index is None:
        return True

    if START_IMAGE_INDEX is not None and image_index < START_IMAGE_INDEX:
        return False

    if END_IMAGE_INDEX is not None and image_index > END_IMAGE_INDEX:
        return False

    return True


def list_image_names() -> list[str]:
    ensure_source_export_extracted()
    image_dir = SOURCE_DIR / "images"
    return sorted(
        [
            path.name
            for path in image_dir.iterdir()
            if path.suffix.lower() in {".png", ".jpg", ".jpeg"}
            and image_is_in_selected_range(path.name)
        ]
    )


def choose_image_name(requested_name: Optional[str]) -> Optional[str]:
    image_names = list_image_names()

    if len(image_names) == 0:
        return None

    if requested_name in image_names:
        return requested_name

    return image_names[0]


def get_next_image_name(current_name: str) -> Optional[str]:
    image_names = list_image_names()

    if current_name not in image_names:
        return None

    next_index = image_names.index(current_name) + 1

    if next_index >= len(image_names):
        return None

    return image_names[next_index]


def image_path_for_name(image_name: str) -> Path:
    return SOURCE_DIR / "images" / image_name


def label_path_for_image(image_name: str) -> Path:
    return SOURCE_DIR / "labels" / f"{Path(image_name).stem}.txt"


def read_champion_boxes(image_name: str, image: Image.Image) -> list[ChampionBox]:
    label_path = label_path_for_image(image_name)

    if not label_path.exists():
        return []

    boxes: list[ChampionBox] = []

    for index, line in enumerate(label_path.read_text(encoding="utf-8").splitlines()):
        parts = line.strip().split()

        if len(parts) != 5:
            continue

        _, center_x_text, center_y_text, width_text, height_text = parts
        center_x = float(center_x_text) * image.width
        center_y = float(center_y_text) * image.height
        box_width = float(width_text) * image.width
        box_height = float(height_text) * image.height
        boxes.append(
            {
                "index": index,
                "x1": center_x - box_width / 2,
                "y1": center_y - box_height / 2,
                "x2": center_x + box_width / 2,
                "y2": center_y + box_height / 2,
            }
        )

    return boxes


def encode_image_as_data_uri(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def read_saved_labels() -> dict[str, str]:
    if not LABELS_JSON.exists():
        return {}

    return json.loads(LABELS_JSON.read_text(encoding="utf-8"))


def write_saved_labels(labels: dict[str, str]) -> None:
    LABELS_JSON.parent.mkdir(parents=True, exist_ok=True)
    LABELS_JSON.write_text(json.dumps(labels, indent=2, sort_keys=True), encoding="utf-8")


def box_key(image_name: str, box_index: int) -> str:
    return f"{image_name}#{box_index}"


def crop_file_name(image_name: str, box_index: int) -> str:
    return f"{Path(image_name).stem}_box_{box_index:03d}.png"


def normalize_champion_name(champion_name: str) -> str:
    normalized = champion_name.strip().lower().replace(" ", "_")

    if normalized == "":
        raise ValueError("Champion name cannot be empty.")

    return normalized


def remove_previous_crop(file_name: str) -> None:
    if not LABELED_DIR.exists():
        return

    for class_dir in LABELED_DIR.iterdir():
        if not class_dir.is_dir():
            continue

        existing_file = class_dir / file_name

        if existing_file.exists():
            existing_file.unlink()


def crop_box(image: Image.Image, box: ChampionBox) -> Image.Image:
    box_width = box["x2"] - box["x1"]
    box_height = box["y2"] - box["y1"]
    padding = max(box_width, box_height) * BOX_PADDING_RATIO
    left = max(0, int(round(box["x1"] - padding)))
    top = max(0, int(round(box["y1"] - padding)))
    right = min(image.width, int(round(box["x2"] + padding)))
    bottom = min(image.height, int(round(box["y2"] + padding)))
    return image.crop((left, top, right, bottom)).convert("RGB")


def save_champion_identity_label(
    image_name: str,
    box_index: int,
    champion_name: str,
) -> dict[str, Any]:
    champion_name = normalize_champion_name(champion_name)
    image = Image.open(image_path_for_name(image_name)).convert("RGB")
    boxes = read_champion_boxes(image_name, image)
    matching_boxes = [box for box in boxes if box["index"] == box_index]

    if len(matching_boxes) == 0:
        raise ValueError(f"Box {box_index} not found for {image_name}")

    file_name = crop_file_name(image_name, box_index)
    output_dir = LABELED_DIR / champion_name
    output_path = output_dir / file_name

    remove_previous_crop(file_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    crop_box(image, matching_boxes[0]).save(output_path)

    labels = read_saved_labels()
    labels[box_key(image_name, box_index)] = champion_name
    write_saved_labels(labels)

    return {
        "champion": champion_name,
        "saved": str(output_path),
    }


def render_page(image_name: str) -> str:
    image = Image.open(image_path_for_name(image_name)).convert("RGB")
    boxes = read_champion_boxes(image_name, image)
    saved_labels = read_saved_labels()
    image_names = list_image_names()
    image_index = image_names.index(image_name) + 1

    box_html = "\n".join(
        f"""
          <g class="champion-box" data-box-index="{box["index"]}">
            <rect
              x="{box["x1"]:.1f}"
              y="{box["y1"]:.1f}"
              width="{box["x2"] - box["x1"]:.1f}"
              height="{box["y2"] - box["y1"]:.1f}"
            />
            <text x="{box["x1"] + 6:.1f}" y="{max(20, box["y1"] - 8):.1f}">
              {escape(saved_labels.get(box_key(image_name, box["index"]), f"box {box['index']}"))}
            </text>
          </g>
        """
        for box in boxes
    )
    options_html = "\n".join(
        f'<option value="{escape(name)}"{" selected" if name == image_name else ""}>{escape(name)}</option>'
        for name in image_names
    )
    champion_options_html = "\n".join(
        f'<option value="{escape(name)}"></option>' for name in CHAMPION_NAMES
    )

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Champion Identity Labeler</title>
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
        max-width: 1280px;
        margin: 0 auto;
        padding: 24px;
      }}

      header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 18px;
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

      input {{
        width: 180px;
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
        fill: rgba(244, 63, 94, 0.16);
        stroke: #f43f5e;
        stroke-width: 3;
        cursor: pointer;
      }}

      .champion-box.saved rect {{
        fill: rgba(15, 118, 110, 0.22);
        stroke: #0f766e;
      }}

      .champion-box text {{
        fill: white;
        stroke: black;
        stroke-width: 4;
        paint-order: stroke;
        font-size: 20px;
        font-weight: 800;
        pointer-events: none;
      }}

      #status {{
        min-height: 22px;
        color: #0f766e;
        font-size: 14px;
        margin: 14px 0 0;
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
        width: min(420px, 100%);
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
          <h1>Champion Identity Labeler</h1>
          <p class="meta">{escape(image_name)} - image {image_index} of {len(image_names)} - {len(boxes)} boxes</p>
        </div>

        <div class="toolbar">
          <select id="imageSelect" aria-label="Choose image">
            {options_html}
          </select>
          <input
            id="championInput"
            list="championNames"
            placeholder="champion name"
            autocomplete="off"
          />
          <datalist id="championNames">
            {champion_options_html}
          </datalist>
          <button class="primary" id="nextButton" type="button">Next image</button>
        </div>
      </header>

      <section class="board" aria-label="Champion boxes">
        <img src="{encode_image_as_data_uri(image)}" alt="{escape(image_name)}" />
        <svg class="overlay" viewBox="0 0 {image.width} {image.height}">
          {box_html}
        </svg>
      </section>

      <p id="status" aria-live="polite"></p>
    </main>

    <div class="dialog-backdrop" id="labelDialog" role="dialog" aria-modal="true">
      <div class="dialog">
        <h2 id="dialogTitle">Champion name</h2>
        <input
          id="dialogChampionInput"
          list="championNames"
          placeholder="search champion"
          autocomplete="off"
        />
        <div class="dialog-actions">
          <button id="cancelLabelButton" type="button">Cancel</button>
          <button class="primary" id="saveLabelButton" type="button">Save</button>
        </div>
      </div>
    </div>

    <script>
      const imageName = {json.dumps(image_name)};
      const nextImageName = {json.dumps(get_next_image_name(image_name))};
      const savedLabels = {json.dumps(saved_labels)};
      const imageSelect = document.querySelector("#imageSelect");
      const championInput = document.querySelector("#championInput");
      const nextButton = document.querySelector("#nextButton");
      const statusText = document.querySelector("#status");
      const labelDialog = document.querySelector("#labelDialog");
      const dialogTitle = document.querySelector("#dialogTitle");
      const dialogChampionInput = document.querySelector("#dialogChampionInput");
      const cancelLabelButton = document.querySelector("#cancelLabelButton");
      const saveLabelButton = document.querySelector("#saveLabelButton");
      let activeBoxGroup = null;
      let activeBoxKey = null;

      function openLabelDialog(boxGroup, key) {{
        activeBoxGroup = boxGroup;
        activeBoxKey = key;
        dialogTitle.textContent = `Champion name for box ${{boxGroup.dataset.boxIndex}}`;
        dialogChampionInput.value = savedLabels[key] || championInput.value || "";
        labelDialog.classList.add("open");
        dialogChampionInput.focus();
        dialogChampionInput.select();
      }}

      function closeLabelDialog() {{
        labelDialog.classList.remove("open");
        activeBoxGroup = null;
        activeBoxKey = null;
      }}

      async function saveActiveLabel() {{
        if (!activeBoxGroup || !activeBoxKey) {{
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
          }}),
        }});
        const result = await response.json();

        if (!response.ok) {{
          statusText.textContent = result.error || "Save failed.";
          return;
        }}

        savedLabels[activeBoxKey] = result.champion;
        activeBoxGroup.classList.add("saved");
        activeBoxGroup.querySelector("text").textContent = result.champion;
        championInput.value = result.champion;
        statusText.textContent = `Saved ${{result.champion}} crop.`;
        closeLabelDialog();
      }}

      document.querySelectorAll(".champion-box").forEach((boxGroup) => {{
        const key = `${{imageName}}#${{boxGroup.dataset.boxIndex}}`;

        if (savedLabels[key]) {{
          boxGroup.classList.add("saved");
        }}

        boxGroup.addEventListener("click", () => {{
          openLabelDialog(boxGroup, key);
        }});
      }});

      cancelLabelButton.addEventListener("click", closeLabelDialog);
      saveLabelButton.addEventListener("click", saveActiveLabel);

      dialogChampionInput.addEventListener("keydown", (event) => {{
        if (event.key === "Enter") {{
          saveActiveLabel();
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
        window.location.href = "/?image=" + encodeURIComponent(imageSelect.value);
      }});

      nextButton.addEventListener("click", () => {{
        if (!nextImageName) {{
          statusText.textContent = "No next image.";
          return;
        }}

        window.location.href = "/?image=" + encodeURIComponent(nextImageName);
      }});
    </script>
  </body>
</html>"""


class ChampionIdentityLabelerHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)

        if parsed_url.path != "/":
            self.send_error(404)
            return

        query = parse_qs(parsed_url.query)
        requested_image = query.get("image", [None])[0]
        image_name = choose_image_name(requested_image)

        if image_name is None:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"No source images found.")
            return

        page = render_page(image_name)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    def do_POST(self) -> None:
        if self.path != "/save":
            self.send_error(404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body)
            result = save_champion_identity_label(
                str(payload["image"]),
                int(payload["box_index"]),
                str(payload["champion"]),
            )
            self.send_response(200)
        except Exception as error:
            result = {"error": str(error)}
            self.send_response(400)

        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode("utf-8"))


def main() -> None:
    global END_IMAGE_INDEX, EXPORT_ZIP, SOURCE_DIR, START_IMAGE_INDEX

    parser = argparse.ArgumentParser()
    parser.add_argument("--export", type=Path, default=EXPORT_ZIP)
    parser.add_argument("--start-image-index", type=int)
    parser.add_argument("--end-image-index", type=int)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    EXPORT_ZIP = args.export
    SOURCE_DIR = DATASET_DIR / "source" / EXPORT_ZIP.stem
    START_IMAGE_INDEX = args.start_image_index
    END_IMAGE_INDEX = args.end_image_index

    ensure_source_export_extracted()
    server = ThreadingHTTPServer(("0.0.0.0", args.port), ChampionIdentityLabelerHandler)
    print(f"Champion identity labeler running at http://localhost:{args.port}")
    print(f"Reading boxes from {EXPORT_ZIP}")
    if START_IMAGE_INDEX is not None or END_IMAGE_INDEX is not None:
        print(f"Image range: {START_IMAGE_INDEX}..{END_IMAGE_INDEX}")
    print(f"Saving crops to {LABELED_DIR}")
    server.serve_forever()


if __name__ == "__main__":
    main()
