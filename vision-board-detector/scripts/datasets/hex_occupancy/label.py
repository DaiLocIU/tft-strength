import base64
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

scripts_dir = Path(__file__).resolve().parents[2]
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

import _bootstrap  # noqa: F401
from PIL import Image

from board_detector.board_geometry import (
    cell_id,
    create_board_hex_cells,
    crop_hex_patch,
    make_tuning_for_image,
    patch_file_name,
    polygon_points_for_svg,
)

CROPS_DIR = Path("outputs/board-crops")
DATASET_DIR = Path("data/hex-occupancy")
OCCUPIED_DIR = DATASET_DIR / "labeled" / "occupied"
EMPTY_DIR = DATASET_DIR / "labeled" / "empty"
MISTAKES_DIR = DATASET_DIR / "mistakes"


def list_board_crop_names() -> list[str]:
    return [path.name for path in sorted(CROPS_DIR.glob("*.png"))]


def read_queue_image_names(queue_name: Optional[str]) -> list[str]:
    if queue_name is None:
        return list_board_crop_names()

    queue_path = MISTAKES_DIR / f"{queue_name}.txt"

    if not queue_path.exists():
        return []

    existing_images = set(list_board_crop_names())
    image_names: list[str] = []

    for line in queue_path.read_text(encoding="utf-8").splitlines():
        image_name = line.strip()

        if image_name in existing_images:
            image_names.append(image_name)

    return image_names


def choose_image_name(requested_name: Optional[str], queue_name: Optional[str]) -> Optional[str]:
    image_names = read_queue_image_names(queue_name)

    if len(image_names) == 0:
        return None

    if requested_name in image_names:
        return requested_name

    return image_names[0]


def get_next_image_name(current_name: str, queue_name: Optional[str]) -> Optional[str]:
    image_names = read_queue_image_names(queue_name)

    if current_name not in image_names:
        return None

    current_index = image_names.index(current_name)
    next_index = current_index + 1

    if next_index >= len(image_names):
        return None

    return image_names[next_index]


def encode_image_as_data_uri(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def remove_previous_labels_for_image(image_name: str) -> None:
    image_stem = Path(image_name).stem
    pattern = f"{image_stem}_r*_c*.png"

    for label_dir in [OCCUPIED_DIR, EMPTY_DIR]:
        label_dir.mkdir(parents=True, exist_ok=True)

        for existing_file in label_dir.glob(pattern):
            existing_file.unlink()


def save_hex_labels(image_name: str, occupied_cell_ids: set[str]) -> dict[str, int]:
    image_path = CROPS_DIR / image_name
    image = Image.open(image_path).convert("RGB")
    hexes = create_board_hex_cells(str(image_path), make_tuning_for_image(image_name))

    remove_previous_labels_for_image(image_name)

    occupied_count = 0
    empty_count = 0

    for hex_cell in hexes:
        patch = crop_hex_patch(image, hex_cell)
        file_name = patch_file_name(image_name, hex_cell)

        if cell_id(hex_cell) in occupied_cell_ids:
            output_path = OCCUPIED_DIR / file_name
            occupied_count += 1
        else:
            output_path = EMPTY_DIR / file_name
            empty_count += 1

        output_path.parent.mkdir(parents=True, exist_ok=True)
        patch.save(output_path)

    return {
        "occupied": occupied_count,
        "empty": empty_count,
    }


def render_page(image_name: str, queue_name: Optional[str]) -> str:
    image_path = CROPS_DIR / image_name
    image = Image.open(image_path).convert("RGB")
    hexes = sorted(
        create_board_hex_cells(str(image_path), make_tuning_for_image(image_name)),
        key=lambda hex_cell: (hex_cell["row"], hex_cell["column"]),
    )
    image_names = read_queue_image_names(queue_name)
    image_index = image_names.index(image_name) + 1
    queue_label = "" if queue_name is None else f" - queue {queue_name}"

    polygons_html = "\n".join(
        f"""
          <polygon
            class="hex-cell"
            data-cell-id="{cell_id(hex_cell)}"
            points="{polygon_points_for_svg(hex_cell)}"
          />
          <text
            class="hex-label"
            x="{hex_cell['center_x']}"
            y="{hex_cell['center_y']}"
          >r{hex_cell['row']} c{hex_cell['column']}</text>
        """
        for hex_cell in hexes
    )

    options_html = "\n".join(
        f'<option value="{name}"{" selected" if name == image_name else ""}>{name}</option>'
        for name in image_names
    )

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Hex Occupancy Labeler</title>
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
        max-width: 1160px;
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

      .toolbar {{
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
      }}

      select,
      button.action {{
        border: 1px solid #c7ccd1;
        border-radius: 6px;
        background: white;
        color: #172026;
        min-height: 38px;
        padding: 0 12px;
        font: inherit;
      }}

      button.action.primary {{
        background: #0f766e;
        border-color: #0f766e;
        color: white;
      }}

      .meta {{
        color: #5f6c7b;
        font-size: 14px;
        margin: 0 0 18px;
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

      .hex-cell {{
        fill: rgba(15, 118, 110, 0.18);
        stroke: #14b8a6;
        stroke-width: 4;
        cursor: pointer;
      }}

      .hex-cell.occupied {{
        fill: rgba(220, 38, 38, 0.42);
        stroke: #dc2626;
      }}

      .hex-label {{
        fill: white;
        stroke: black;
        stroke-width: 3;
        paint-order: stroke;
        font-size: 18px;
        font-weight: 700;
        pointer-events: none;
        text-anchor: middle;
        dominant-baseline: middle;
      }}

      #status {{
        min-height: 20px;
        color: #0f766e;
        font-size: 14px;
      }}

      @media (max-width: 760px) {{
        main {{
          padding: 14px;
        }}

        header {{
          align-items: flex-start;
          flex-direction: column;
        }}

        .hex-label {{
          font-size: 24px;
        }}
      }}
    </style>
  </head>
  <body>
    <main>
      <header>
        <div>
          <h1>Hex Occupancy Labeler</h1>
          <p class="meta">
            {image_name} - image {image_index} of {len(image_names)}{queue_label} -
            click only occupied hexes
          </p>
        </div>

        <div class="toolbar">
          <select id="imageSelect" aria-label="Choose board crop">
            {options_html}
          </select>
          <button class="action" id="clearButton" type="button">Clear</button>
          <button class="action primary" id="saveButton" type="button">Save labels</button>
        </div>
      </header>

      <section class="board" aria-label="Board crop">
        <img src="{encode_image_as_data_uri(image)}" alt="{image_name}" />
        <svg
          class="overlay"
          viewBox="0 0 {image.width} {image.height}"
          aria-label="Clickable board hexes"
        >
          {polygons_html}
        </svg>
      </section>

      <p id="status" aria-live="polite"></p>
    </main>

    <script>
      const imageName = {json.dumps(image_name)};
      const queueName = {json.dumps(queue_name)};
      const imageSelect = document.querySelector("#imageSelect");
      const clearButton = document.querySelector("#clearButton");
      const saveButton = document.querySelector("#saveButton");
      const statusText = document.querySelector("#status");

      document.querySelectorAll(".hex-cell").forEach((polygon) => {{
        polygon.addEventListener("click", () => {{
          polygon.classList.toggle("occupied");
        }});
      }});

      imageSelect.addEventListener("change", () => {{
        let nextUrl = "/?image=" + encodeURIComponent(imageSelect.value);

        if (queueName) {{
          nextUrl += "&queue=" + encodeURIComponent(queueName);
        }}

        window.location.href = nextUrl;
      }});

      clearButton.addEventListener("click", () => {{
        document.querySelectorAll(".hex-cell.occupied").forEach((polygon) => {{
          polygon.classList.remove("occupied");
        }});
      }});

      saveButton.addEventListener("click", async () => {{
        const occupied = Array.from(
          document.querySelectorAll(".hex-cell.occupied")
        ).map((polygon) => {{
          return polygon.dataset.cellId;
        }});

        const response = await fetch("/save", {{
          method: "POST",
          headers: {{"Content-Type": "application/json"}},
          body: JSON.stringify({{image: imageName, occupied, queue: queueName}}),
        }});
        const result = await response.json();
        statusText.textContent =
          `Saved ${{result.occupied}} occupied and ${{result.empty}} empty patches.`;

        if (result.next_image) {{
          window.setTimeout(() => {{
            let nextUrl = "/?image=" + encodeURIComponent(result.next_image);

            if (queueName) {{
              nextUrl += "&queue=" + encodeURIComponent(queueName);
            }}

            window.location.href = nextUrl;
          }}, 450);
        }}
      }});
    </script>
  </body>
</html>"""


class LabelHexOccupancyHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)

        if parsed_url.path != "/":
            self.send_error(404)
            return

        query = parse_qs(parsed_url.query)
        requested_image = query.get("image", [None])[0]
        queue_name = query.get("queue", [None])[0]
        image_name = choose_image_name(requested_image, queue_name)

        if image_name is None:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"No board crops found for this queue.")
            return

        page = render_page(image_name, queue_name)
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
        payload = json.loads(body)
        image_name = str(payload["image"])
        queue_name = payload.get("queue")
        queue_name = None if queue_name is None else str(queue_name)
        occupied_cell_ids = {str(cell_id_value) for cell_id_value in payload["occupied"]}

        counts = save_hex_labels(image_name, occupied_cell_ids)
        next_image_name = get_next_image_name(image_name, queue_name)
        response: dict[str, Any] = {
            "occupied": counts["occupied"],
            "empty": counts["empty"],
            "next_image": next_image_name,
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))


def main() -> None:
    server = HTTPServer(("localhost", 8091), LabelHexOccupancyHandler)
    print("Hex occupancy labeler running at http://localhost:8091")
    print(f"Saving patches to {DATASET_DIR}")
    server.serve_forever()


if __name__ == "__main__":
    main()
