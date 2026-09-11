import argparse
import base64
import json
import shutil
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from typing import Any, Optional, TypedDict
from urllib.parse import parse_qs, unquote, urlparse

from PIL import Image

SOURCE_DIR = Path("data/champion-star/source").resolve()
DATASET_DIR = Path("data/champion-star").resolve()
LABELED_DIR = DATASET_DIR / "labeled"
LABELS_JSON = DATASET_DIR / "star-labels.json"
DEFAULT_PORT = 8096
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
STAR_LABELS = ["1star", "2star", "3star", "unknown"]


class StarLabelRecord(TypedDict):
    crop_path: str
    star_label: str


def encode_image_as_data_uri(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def crop_key(crop_path: Path) -> str:
    return str(crop_path.resolve().relative_to(SOURCE_DIR))


def crop_image_index(crop_path: Path) -> Optional[int]:
    parts = crop_path.name.split("_")
    if len(parts) < 2 or parts[0] != "image":
        return None

    try:
        return int(parts[1])
    except ValueError:
        return None


def crop_matches_index_range(
    crop_path: Path,
    start_index: Optional[int],
    end_index: Optional[int],
) -> bool:
    image_index = crop_image_index(crop_path)
    if image_index is None:
        return False
    if start_index is not None and image_index < start_index:
        return False
    return not (end_index is not None and image_index > end_index)


def read_labels() -> dict[str, StarLabelRecord]:
    if not LABELS_JSON.exists():
        return {}

    return json.loads(LABELS_JSON.read_text(encoding="utf-8"))


def write_labels(labels: dict[str, StarLabelRecord]) -> None:
    LABELS_JSON.parent.mkdir(parents=True, exist_ok=True)
    LABELS_JSON.write_text(json.dumps(labels, indent=2, sort_keys=True), encoding="utf-8")


def ensure_label_dirs() -> None:
    for star_label in STAR_LABELS:
        (LABELED_DIR / star_label).mkdir(parents=True, exist_ok=True)


def list_crop_paths(
    show_labeled: bool,
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
) -> list[Path]:
    labels = read_labels()
    return sorted(
        [
            path
            for path in SOURCE_DIR.rglob("*")
            if path.is_file()
            and path.suffix.lower() in IMAGE_EXTENSIONS
            and crop_matches_index_range(path, start_index, end_index)
            and (show_labeled or crop_key(path) not in labels)
        ],
        key=crop_key,
    )


def choose_crop_path(
    requested_crop: Optional[str],
    show_labeled: bool,
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
) -> Optional[Path]:
    crop_paths = list_crop_paths(show_labeled, start_index, end_index)

    if len(crop_paths) == 0:
        return None

    if requested_crop is not None:
        requested_path = (SOURCE_DIR / unquote(requested_crop)).resolve()

        for crop_path in crop_paths:
            if crop_path.resolve() == requested_path:
                return crop_path

    return crop_paths[0]


def get_next_crop_path(
    current_crop: Path,
    show_labeled: bool,
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
) -> Optional[Path]:
    crop_paths = list_crop_paths(show_labeled, start_index, end_index)
    current_key = crop_key(current_crop)
    keys = [crop_key(path) for path in crop_paths]

    if current_key not in keys:
        return crop_paths[0] if len(crop_paths) > 0 else None

    next_index = keys.index(current_key) + 1

    if next_index >= len(crop_paths):
        return None

    return crop_paths[next_index]


def remove_previous_labeled_crop(file_name: str) -> None:
    if not LABELED_DIR.exists():
        return

    for class_dir in LABELED_DIR.iterdir():
        if not class_dir.is_dir():
            continue

        existing_file = class_dir / file_name

        if existing_file.exists():
            existing_file.unlink()


def save_star_label(crop_path: Path, star_label: str) -> dict[str, Any]:
    normalized_label = star_label.strip().lower()

    if normalized_label not in STAR_LABELS:
        raise ValueError(f"Unknown star label: {star_label}")

    output_dir = LABELED_DIR / normalized_label
    output_path = output_dir / crop_path.name

    remove_previous_labeled_crop(crop_path.name)
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(crop_path, output_path)

    labels = read_labels()
    labels[crop_key(crop_path)] = {
        "crop_path": str(crop_path),
        "star_label": normalized_label,
    }
    write_labels(labels)

    return {
        "star_label": normalized_label,
        "saved": str(output_path),
    }


def render_page(
    crop_path: Path,
    show_labeled: bool,
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
) -> str:
    crop_paths = list_crop_paths(show_labeled, start_index, end_index)
    crop_paths_by_key = {crop_key(path): path for path in crop_paths}
    current_key = crop_key(crop_path)
    current_index = list(crop_paths_by_key).index(current_key) + 1
    next_crop_path = get_next_crop_path(crop_path, show_labeled, start_index, end_index)
    next_crop_key = crop_key(next_crop_path) if next_crop_path is not None else None
    image = Image.open(crop_path).convert("RGB")
    index_range_text = (
        f" - image {start_index}-{end_index}"
        if start_index is not None and end_index is not None
        else ""
    )
    meta_text = f"Crop {current_index} of {len(crop_paths)}{index_range_text} - {current_key}"
    crop_options_html = "\n".join(
        f'<option value="{escape(key)}"{" selected" if key == current_key else ""}>'
        f"{escape(key)}</option>"
        for key in crop_paths_by_key
    )
    buttons_html = "\n".join(
        f'<button class="label-button" data-label="{label}" type="button">{label}</button>'
        for label in STAR_LABELS
    )

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Champion Star Labeler</title>
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
        max-width: 980px;
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

      .toolbar,
      .actions {{
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
      }}

      select,
      button,
      label {{
        min-height: 38px;
        border: 1px solid #c7ccd1;
        border-radius: 6px;
        background: white;
        color: #172026;
        padding: 0 12px;
        font: inherit;
      }}

      select {{
        max-width: 340px;
      }}

      label {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
      }}

      button.primary,
      .label-button {{
        background: #0f766e;
        border-color: #0f766e;
        color: white;
        font-weight: 700;
      }}

      .crop {{
        display: grid;
        place-items: center;
        min-height: 420px;
        border: 1px solid #c7ccd1;
        border-radius: 8px;
        background: #111827;
        padding: 18px;
      }}

      .crop img {{
        max-width: min(100%, 560px);
        max-height: 640px;
        image-rendering: auto;
      }}

      .actions {{
        justify-content: center;
        margin-top: 16px;
      }}

      #status {{
        min-height: 22px;
        color: #0f766e;
        font-size: 14px;
        margin: 12px 0 0;
        text-align: center;
      }}
    </style>
  </head>
  <body>
    <main>
      <header>
        <div>
          <h1>Champion Star Labeler</h1>
          <p class="meta">{escape(meta_text)}</p>
        </div>
        <div class="toolbar">
          <select id="cropSelect" aria-label="Choose crop">
            {crop_options_html}
          </select>
          <label>
            <input id="showLabeled" type="checkbox" {"checked" if show_labeled else ""} />
            show labeled
          </label>
          <button class="primary" id="nextButton" type="button">Next</button>
        </div>
      </header>

      <section class="crop" aria-label="Champion star crop">
        <img src="{encode_image_as_data_uri(image)}" alt="{escape(current_key)}" />
      </section>

      <div class="actions">
        {buttons_html}
      </div>
      <p id="status" aria-live="polite"></p>
    </main>

    <script>
      const currentCrop = {json.dumps(current_key)};
      const nextCrop = {json.dumps(next_crop_key)};
      const startIndex = {json.dumps(start_index)};
      const endIndex = {json.dumps(end_index)};
      const showLabeled = document.querySelector("#showLabeled");
      const cropSelect = document.querySelector("#cropSelect");
      const nextButton = document.querySelector("#nextButton");
      const statusText = document.querySelector("#status");

      function urlForCrop(crop) {{
        const params = new URLSearchParams();
        params.set("crop", crop);

        if (showLabeled.checked) {{
          params.set("show_labeled", "1");
        }}
        if (startIndex !== null) {{
          params.set("start_index", startIndex);
        }}
        if (endIndex !== null) {{
          params.set("end_index", endIndex);
        }}

        return "/?" + params.toString();
      }}

      async function saveLabel(starLabel) {{
        const response = await fetch("/save", {{
          method: "POST",
          headers: {{"Content-Type": "application/json"}},
          body: JSON.stringify({{
            crop: currentCrop,
            star_label: starLabel,
            show_labeled: showLabeled.checked,
            start_index: startIndex,
            end_index: endIndex,
          }}),
        }});
        const result = await response.json();

        if (!response.ok) {{
          statusText.textContent = result.error || "Save failed.";
          return;
        }}

        statusText.textContent = `Saved ${{result.star_label}}`;

        if (result.next_crop) {{
          window.location.href = urlForCrop(result.next_crop);
        }}
      }}

      document.querySelectorAll(".label-button").forEach((button) => {{
        button.addEventListener("click", () => saveLabel(button.dataset.label));
      }});
      cropSelect.addEventListener("change", () => {{
        window.location.href = urlForCrop(cropSelect.value);
      }});
      showLabeled.addEventListener("change", () => {{
        window.location.href = urlForCrop(currentCrop);
      }});
      nextButton.addEventListener("click", () => {{
        if (!nextCrop) {{
          statusText.textContent = "No next crop.";
          return;
        }}

        window.location.href = urlForCrop(nextCrop);
      }});
      window.addEventListener("keydown", (event) => {{
        if (event.key === "1") saveLabel("1star");
        if (event.key === "2") saveLabel("2star");
        if (event.key === "3") saveLabel("3star");
        if (event.key.toLowerCase() === "u") saveLabel("unknown");
      }});
    </script>
  </body>
</html>"""


class ChampionStarLabelHandler(BaseHTTPRequestHandler):
    show_labeled = False
    start_index: Optional[int] = None
    end_index: Optional[int] = None

    def send_json(self, status_code: int, body: dict[str, Any]) -> None:
        encoded_body = json.dumps(body).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded_body)))
        self.end_headers()
        self.wfile.write(encoded_body)

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)

        if parsed_url.path != "/":
            self.send_error(404)
            return

        query = parse_qs(parsed_url.query)
        show_labeled = query.get("show_labeled", ["1" if self.show_labeled else "0"])[0] == "1"
        start_index = int(query["start_index"][0]) if "start_index" in query else self.start_index
        end_index = int(query["end_index"][0]) if "end_index" in query else self.end_index
        requested_crop = query.get("crop", [None])[0]
        crop_path = choose_crop_path(requested_crop, show_labeled, start_index, end_index)

        if crop_path is None:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"No champion star crops found. Run collect_champion_star_crops.py.")
            return

        try:
            page = render_page(crop_path, show_labeled, start_index, end_index)
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
            show_labeled = bool(payload.get("show_labeled", self.show_labeled))
            start_index = payload.get("start_index", self.start_index)
            end_index = payload.get("end_index", self.end_index)
            crop_path = choose_crop_path(str(payload["crop"]), show_labeled=True)

            if crop_path is None:
                raise FileNotFoundError(f"Crop not found: {payload['crop']}")

            result = save_star_label(crop_path, str(payload["star_label"]))
            next_crop_path = get_next_crop_path(crop_path, show_labeled, start_index, end_index)
            result["next_crop"] = crop_key(next_crop_path) if next_crop_path is not None else None
            self.send_json(200, result)
        except Exception as error:
            self.send_json(400, {"error": str(error)})

    def log_message(self, format_text: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format_text % args}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--show-labeled", action="store_true")
    parser.add_argument("--start-index", type=int)
    parser.add_argument("--end-index", type=int)
    args = parser.parse_args()

    ensure_label_dirs()
    ChampionStarLabelHandler.show_labeled = args.show_labeled
    ChampionStarLabelHandler.start_index = args.start_index
    ChampionStarLabelHandler.end_index = args.end_index
    server = ThreadingHTTPServer(("127.0.0.1", args.port), ChampionStarLabelHandler)
    print(f"Champion star labeler: http://127.0.0.1:{args.port}")
    print(f"Reading crops from {SOURCE_DIR}")
    print(f"Saving labels to {LABELED_DIR}")
    server.serve_forever()


if __name__ == "__main__":
    main()
