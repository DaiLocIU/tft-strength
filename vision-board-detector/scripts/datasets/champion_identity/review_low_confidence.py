import argparse
import base64
import json
import shutil
import sys
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from typing import Any, Optional, TypedDict
from urllib.parse import parse_qs, unquote, urlparse

scripts_dir = Path(__file__).resolve().parents[2]
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from datasets.champion_identity.label import CHAMPION_NAMES, normalize_champion_name
from PIL import Image


DATASET_DIR = Path("data/champion-identity").resolve()
REVIEW_DIR = DATASET_DIR / "review-low-confidence"
LABELED_DIR = DATASET_DIR / "labeled"
REVIEWED_JSON = REVIEW_DIR / "reviewed-labels.json"
DEFAULT_PORT = 8093
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


class ReviewRecord(TypedDict):
    crop_path: str
    champion: str
    action: str


def encode_image_as_data_uri(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def read_reviewed_labels() -> dict[str, ReviewRecord]:
    if not REVIEWED_JSON.exists():
        return {}

    return json.loads(REVIEWED_JSON.read_text(encoding="utf-8"))


def write_reviewed_labels(labels: dict[str, ReviewRecord]) -> None:
    REVIEWED_JSON.parent.mkdir(parents=True, exist_ok=True)
    REVIEWED_JSON.write_text(json.dumps(labels, indent=2, sort_keys=True), encoding="utf-8")


def crop_key(crop_path: Path) -> str:
    return str(crop_path.resolve().relative_to(REVIEW_DIR.resolve()))


def list_review_crop_paths(show_reviewed: bool) -> list[Path]:
    reviewed_labels = read_reviewed_labels()

    crop_paths = sorted(
        [
            path
            for path in REVIEW_DIR.rglob("*")
            if path.is_file()
            and path.suffix.lower() in IMAGE_EXTENSIONS
            and (show_reviewed or crop_key(path) not in reviewed_labels)
        ],
        key=lambda path: crop_key(path),
    )
    return crop_paths


def choose_crop_path(requested_crop: Optional[str], show_reviewed: bool) -> Optional[Path]:
    crop_paths = list_review_crop_paths(show_reviewed)

    if len(crop_paths) == 0:
        return None

    if requested_crop is not None:
        requested_path = (REVIEW_DIR / unquote(requested_crop)).resolve()

        for crop_path in crop_paths:
            if crop_path.resolve() == requested_path:
                return crop_path

    return crop_paths[0]


def get_next_crop_path(current_crop: Path, show_reviewed: bool) -> Optional[Path]:
    crop_paths = list_review_crop_paths(show_reviewed)
    current_key = crop_key(current_crop)
    keys = [crop_key(path) for path in crop_paths]

    if current_key not in keys:
        return crop_paths[0] if len(crop_paths) > 0 else None

    next_index = keys.index(current_key) + 1

    if next_index >= len(crop_paths):
        return None

    return crop_paths[next_index]


def output_file_name(crop_path: Path) -> str:
    return crop_path.name


def remove_previous_labeled_crop(file_name: str) -> None:
    if not LABELED_DIR.exists():
        return

    for class_dir in LABELED_DIR.iterdir():
        if not class_dir.is_dir():
            continue

        existing_file = class_dir / file_name

        if existing_file.exists():
            existing_file.unlink()


def save_reviewed_crop(crop_path: Path, champion_name: str) -> dict[str, Any]:
    normalized_name = normalize_champion_name(champion_name)
    file_name = output_file_name(crop_path)
    output_dir = LABELED_DIR / normalized_name
    output_path = output_dir / file_name

    remove_previous_labeled_crop(file_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(crop_path, output_path)

    labels = read_reviewed_labels()
    labels[crop_key(crop_path)] = {
        "crop_path": str(crop_path),
        "champion": normalized_name,
        "action": "labeled",
    }
    write_reviewed_labels(labels)

    return {
        "champion": normalized_name,
        "saved": str(output_path),
    }


def skip_reviewed_crop(crop_path: Path) -> dict[str, Any]:
    labels = read_reviewed_labels()
    labels[crop_key(crop_path)] = {
        "crop_path": str(crop_path),
        "champion": "unknown",
        "action": "skipped",
    }
    write_reviewed_labels(labels)

    return {"skipped": crop_key(crop_path)}


def render_page(crop_path: Path, show_reviewed: bool) -> str:
    crop_paths = list_review_crop_paths(show_reviewed)
    crop_paths_by_key = {crop_key(path): path for path in crop_paths}
    current_key = crop_key(crop_path)
    current_index = list(crop_paths_by_key).index(current_key) + 1
    next_crop_path = get_next_crop_path(crop_path, show_reviewed)
    next_crop_key = crop_key(next_crop_path) if next_crop_path is not None else None
    predicted_name = crop_path.parent.name
    image = Image.open(crop_path).convert("RGB")
    champion_options_html = "\n".join(
        f'<option value="{escape(name)}"></option>' for name in CHAMPION_NAMES
    )
    crop_options_html = "\n".join(
        f'<option value="{escape(key)}"{" selected" if key == current_key else ""}>{escape(key)}</option>'
        for key in crop_paths_by_key
    )

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Low Confidence Champion Review</title>
    <style>
      * {{
        box-sizing: border-box;
      }}

      body {{
        margin: 0;
        background: #f7f5ef;
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
        max-width: 1120px;
        margin: 0 auto;
        padding: 24px;
      }}

      header {{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 18px;
      }}

      h1 {{
        font-size: 24px;
        margin: 0 0 4px;
      }}

      .meta {{
        margin: 0;
        color: #5f6c7b;
        font-size: 14px;
      }}

      .toolbar {{
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 10px;
      }}

      select,
      input,
      button {{
        min-height: 40px;
        border: 1px solid #c7ccd1;
        border-radius: 6px;
        background: white;
        color: #172026;
        padding: 0 12px;
        font: inherit;
      }}

      select {{
        width: min(420px, 100%);
      }}

      input {{
        width: 240px;
      }}

      button.primary {{
        background: #0f766e;
        border-color: #0f766e;
        color: white;
      }}

      button.secondary {{
        background: #fff7ed;
        border-color: #fdba74;
        color: #9a3412;
      }}

      .crop-panel {{
        display: grid;
        grid-template-columns: minmax(260px, 520px) 1fr;
        gap: 24px;
        align-items: start;
      }}

      .crop-frame {{
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 460px;
        border: 1px solid #c7ccd1;
        border-radius: 8px;
        background: #111827;
        padding: 18px;
      }}

      .crop-frame img {{
        max-width: 100%;
        max-height: 680px;
        image-rendering: auto;
      }}

      .details {{
        border-top: 1px solid #d7dce2;
        padding-top: 18px;
      }}

      .details code {{
        display: block;
        overflow-wrap: anywhere;
        background: #edf2f7;
        padding: 10px;
        border-radius: 6px;
      }}

      #status {{
        min-height: 22px;
        margin-top: 14px;
        color: #0f766e;
        font-size: 14px;
      }}

      @media (max-width: 820px) {{
        .crop-panel {{
          grid-template-columns: 1fr;
        }}

        header {{
          display: block;
        }}

        .toolbar {{
          margin-top: 14px;
        }}
      }}
    </style>
  </head>
  <body>
    <main>
      <header>
        <div>
          <h1>Low Confidence Champion Review</h1>
          <p class="meta">Crop {current_index} of {len(crop_paths)} - predicted {escape(predicted_name)}</p>
        </div>
        <div class="toolbar">
          <select id="cropSelect" aria-label="Choose crop">
            {crop_options_html}
          </select>
          <input
            id="championInput"
            list="championNames"
            value="{escape(predicted_name)}"
            placeholder="champion name"
            autocomplete="off"
          />
          <datalist id="championNames">
            {champion_options_html}
          </datalist>
          <button class="primary" id="saveButton" type="button">Save label</button>
          <button class="secondary" id="skipButton" type="button">Skip</button>
          <button id="nextButton" type="button">Next</button>
        </div>
      </header>

      <section class="crop-panel">
        <div class="crop-frame">
          <img src="{encode_image_as_data_uri(image)}" alt="{escape(current_key)}" />
        </div>
        <div class="details">
          <p class="meta">Current crop</p>
          <code>{escape(current_key)}</code>
          <p class="meta">Tip: choose the true champion name. Use <strong>Unknown</strong> for bad detector boxes, UI, effects, or unclear crops.</p>
          <p id="status" aria-live="polite"></p>
        </div>
      </section>
    </main>

    <script>
      const cropKey = {json.dumps(current_key)};
      const nextCropKey = {json.dumps(next_crop_key)};
      const showReviewed = {json.dumps(show_reviewed)};
      const cropSelect = document.querySelector("#cropSelect");
      const championInput = document.querySelector("#championInput");
      const saveButton = document.querySelector("#saveButton");
      const skipButton = document.querySelector("#skipButton");
      const nextButton = document.querySelector("#nextButton");
      const statusText = document.querySelector("#status");

      function cropUrl(key) {{
        const params = new URLSearchParams();
        params.set("crop", key);

        if (showReviewed) {{
          params.set("show_reviewed", "1");
        }}

        return "/?" + params.toString();
      }}

      function goNext() {{
        if (!nextCropKey) {{
          statusText.textContent = "No next crop.";
          return;
        }}

        window.location.href = cropUrl(nextCropKey);
      }}

      async function postJson(path, payload) {{
        const response = await fetch(path, {{
          method: "POST",
          headers: {{"Content-Type": "application/json"}},
          body: JSON.stringify(payload),
        }});
        const result = await response.json();

        if (!response.ok) {{
          throw new Error(result.error || "Save failed.");
        }}

        return result;
      }}

      saveButton.addEventListener("click", async () => {{
        const championName = championInput.value.trim();

        if (!championName) {{
          statusText.textContent = "Choose or type a champion name.";
          return;
        }}

        try {{
          const result = await postJson("/save", {{
            crop: cropKey,
            champion: championName,
          }});
          statusText.textContent = `Saved ${{result.champion}}.`;
          setTimeout(goNext, 180);
        }} catch (error) {{
          statusText.textContent = error.message;
        }}
      }});

      skipButton.addEventListener("click", async () => {{
        try {{
          await postJson("/skip", {{crop: cropKey}});
          statusText.textContent = "Skipped.";
          setTimeout(goNext, 180);
        }} catch (error) {{
          statusText.textContent = error.message;
        }}
      }});

      nextButton.addEventListener("click", goNext);

      championInput.addEventListener("keydown", (event) => {{
        if (event.key === "Enter") {{
          saveButton.click();
        }}
      }});

      cropSelect.addEventListener("change", () => {{
        window.location.href = cropUrl(cropSelect.value);
      }});
    </script>
  </body>
</html>"""


def crop_path_from_payload(payload: dict[str, Any]) -> Path:
    crop_value = str(payload["crop"])
    crop_path = (REVIEW_DIR / crop_value).resolve()
    review_root = REVIEW_DIR.resolve()

    if crop_path != review_root and review_root not in crop_path.parents:
        raise ValueError("Crop path must stay inside review directory.")

    if not crop_path.exists():
        raise FileNotFoundError(f"Crop not found: {crop_value}")

    return crop_path


class LowConfidenceChampionReviewHandler(BaseHTTPRequestHandler):
    show_reviewed: bool = False

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)

        if parsed_url.path != "/":
            self.send_error(404)
            return

        query = parse_qs(parsed_url.query)
        show_reviewed = self.show_reviewed or query.get("show_reviewed", ["0"])[0] == "1"
        requested_crop = query.get("crop", [None])[0]
        crop_path = choose_crop_path(requested_crop, show_reviewed)

        if crop_path is None:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"No low-confidence crops found.")
            return

        page = render_page(crop_path, show_reviewed)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    def do_POST(self) -> None:
        if self.path not in {"/save", "/skip"}:
            self.send_error(404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body)
            crop_path = crop_path_from_payload(payload)

            if self.path == "/save":
                result = save_reviewed_crop(crop_path, str(payload["champion"]))
            else:
                result = skip_reviewed_crop(crop_path)

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
    parser.add_argument("--show-reviewed", action="store_true")
    args = parser.parse_args()

    if not REVIEW_DIR.exists():
        raise FileNotFoundError(f"Review directory not found: {REVIEW_DIR}")

    LowConfidenceChampionReviewHandler.show_reviewed = args.show_reviewed
    server = ThreadingHTTPServer(("0.0.0.0", args.port), LowConfidenceChampionReviewHandler)
    print(f"Low-confidence champion review running at http://localhost:{args.port}")
    print(f"Reading crops from {REVIEW_DIR}")
    print(f"Saving corrected labels to {LABELED_DIR}")
    print(f"Reviewed records at {REVIEWED_JSON}")
    server.serve_forever()


if __name__ == "__main__":
    main()
