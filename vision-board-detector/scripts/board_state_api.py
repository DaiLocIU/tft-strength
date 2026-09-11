import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional, cast
from urllib.parse import parse_qs, urlparse

import _bootstrap  # noqa: F401
from combine_hex_signals import (
    BOARD_STATE_OUTPUT_DIR,
    CHAMPION_CONFIDENCE,
    CHAMPION_IDENTITY_MODEL_PATH,
    CHAMPION_IDENTITY_PADDING_RATIO,
    CHAMPION_MODEL_PATH,
    CHAMPION_STAR_MODEL_PATH,
    CROPS_DIR,
    HEX_OCCUPANCY_MODEL_PATH,
    IDENTITY_CONFIDENCE_THRESHOLD,
    combine_hex_signals_for_image,
)
from board_detector.hud_ocr import detect_hud
from PIL import Image
from predict_board import crop_board, detect_board
from review.review_combined_champion_names import save_corrected_name
from ultralytics import YOLO  # type: ignore[attr-defined]

from board_detector.board_geometry import (
    HexCell,
    create_board_hex_cells,
    crop_hex_patch,
    make_tuning_for_image,
    patch_file_name,
)
from board_detector.board_geometry import (
    find_hex_cell as find_hex_cell_in_grid,
)

DEFAULT_PORT = 8095
RAW_DIR = Path("data/raw")
CORRECTIONS_DIR = Path("data/corrections")
BOARD_STATE_CORRECTIONS_DIR = CORRECTIONS_DIR / "board-state"
HEX_OCCUPANCY_CORRECTIONS_DIR = CORRECTIONS_DIR / "hex-occupancy"
CHAMPION_DETECTOR_CORRECTIONS_PATH = CORRECTIONS_DIR / "champion-detector" / "missing-boxes.jsonl"
CHAMPION_IDENTITY_CORRECTIONS_PATH = (
    CORRECTIONS_DIR / "champion-identity" / "manual-missing-hex.jsonl"
)
RETRAIN_LOG_DIR = Path("outputs/retrain-logs")

hex_occupancy_model: Optional[YOLO] = None
champion_model: Optional[YOLO] = None
identity_model: Optional[YOLO] = None
star_model: Optional[YOLO] = None
champion_star_retrain_process: Optional[subprocess.Popen[bytes]] = None
champion_star_retrain_log_path: Optional[Path] = None
champion_star_retrain_run_name: Optional[str] = None


def get_models() -> tuple[YOLO, YOLO, YOLO, YOLO]:
    global champion_model, hex_occupancy_model, identity_model, star_model

    if hex_occupancy_model is None:
        hex_occupancy_model = YOLO(HEX_OCCUPANCY_MODEL_PATH)

    if champion_model is None:
        champion_model = YOLO(CHAMPION_MODEL_PATH)

    if identity_model is None:
        identity_model = YOLO(CHAMPION_IDENTITY_MODEL_PATH)

    star_model = YOLO(CHAMPION_STAR_MODEL_PATH)

    return hex_occupancy_model, champion_model, identity_model, star_model


def first_query_value(query: dict[str, list[str]], name: str, default: str) -> str:
    values = query.get(name)

    if values is None or len(values) == 0:
        return default

    return values[0]


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as output_file:
        output_file.write(json.dumps(record, sort_keys=True))
        output_file.write("\n")


def read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    content_length = int(handler.headers.get("Content-Length", "0"))

    if content_length <= 0:
        return {}

    raw_body = handler.rfile.read(content_length)
    return cast(dict[str, Any], json.loads(raw_body.decode("utf-8")))


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "occupied"}

    return bool(value)


def find_hex_cell(image_name: str, row: int, column: int) -> HexCell:
    board_crop_path = CROPS_DIR / image_name
    hexes = create_board_hex_cells(str(board_crop_path), make_tuning_for_image(image_name))
    return find_hex_cell_in_grid(hexes, row, column)


def save_hex_occupancy_correction(
    image_name: str,
    row: int,
    column: int,
    occupied: bool,
) -> dict[str, Any]:
    board_crop_path = CROPS_DIR / image_name

    if not board_crop_path.exists():
        raise FileNotFoundError(f"Board crop not found: {board_crop_path}")

    hex_cell = find_hex_cell(image_name, row, column)
    board_image = Image.open(board_crop_path).convert("RGB")
    patch = crop_hex_patch(board_image, hex_cell)
    label = "occupied" if occupied else "empty"
    output_path = HEX_OCCUPANCY_CORRECTIONS_DIR / label / patch_file_name(image_name, hex_cell)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    patch.save(output_path)

    return {
        "image_name": image_name,
        "row": row,
        "column": column,
        "occupied": occupied,
        "hex_crop_path": str(output_path),
    }


def save_missing_hex_correction(payload: dict[str, Any]) -> dict[str, Any]:
    image_name = str(payload["image_name"])
    row = int(payload["row"])
    column = int(payload["column"])
    champion = str(payload.get("champion", "unknown"))
    hex_record = save_hex_occupancy_correction(image_name, row, column, True)
    record = {
        **hex_record,
        "champion": champion,
        "correction_type": "missing_hex",
        "needs_champion_box_label": True,
        "needs_identity_crop": True,
    }
    board_state_path = BOARD_STATE_CORRECTIONS_DIR / f"{Path(image_name).stem}.jsonl"
    append_jsonl(board_state_path, record)
    append_jsonl(CHAMPION_DETECTOR_CORRECTIONS_PATH, record)
    append_jsonl(CHAMPION_IDENTITY_CORRECTIONS_PATH, record)

    return {
        "saved": record,
        "board_state_correction_path": str(board_state_path),
        "champion_detector_correction_path": str(CHAMPION_DETECTOR_CORRECTIONS_PATH),
        "champion_identity_correction_path": str(CHAMPION_IDENTITY_CORRECTIONS_PATH),
    }


def retrain_commands() -> dict[str, list[str]]:
    return {
        "hex_occupancy": [
            "copy reviewed data/corrections/hex-occupancy/occupied crops into "
            "data/hex-occupancy/labeled/occupied when they are correct",
            "copy reviewed data/corrections/hex-occupancy/empty crops into "
            "data/hex-occupancy/labeled/empty when they are correct",
            ".venv/bin/python scripts/datasets/hex_occupancy/split.py",
            "yolo classify train model=models/hex-occupancy-classifier.pt "
            "data=data/hex-occupancy imgsz=96 epochs=50 device=mps "
            "project=../runs/classify name=hex-occupancy-after-api-review",
            "cp ../runs/classify/hex-occupancy-after-api-review/weights/best.pt "
            "models/hex-occupancy-classifier.pt",
        ],
        "champion_detector": [
            "use data/corrections/champion-detector/missing-boxes.jsonl as the "
            "todo list for missing boxes",
            "label those missing champion boxes in Label Studio and export YOLO format",
            ".venv/bin/python scripts/datasets/champion_detector/prepare.py "
            "--export exports/label-studio/<new-export>.zip",
            "yolo detect train model=models/champion-detector.pt "
            "data=data/champion-detector/data.yaml imgsz=640 epochs=100 "
            "device=mps project=../runs/detect name=champion-detector-after-api-review",
            "cp ../runs/detect/champion-detector-after-api-review/weights/best.pt "
            "models/champion-detector.pt",
        ],
        "champion_identity": [
            "corrected board clicks already save crops into "
            "data/champion-identity/labeled/<champion>",
            ".venv/bin/python scripts/datasets/champion_identity/split.py",
            "yolo classify train model=models/champion-identity-classifier.pt "
            "data=data/champion-identity imgsz=160 epochs=100 device=mps "
            "project=../runs/classify name=champion-identity-after-api-review",
            "cp ../runs/classify/champion-identity-after-api-review/weights/best.pt "
            "models/champion-identity-classifier.pt",
        ],
        "champion_star": [
            "corrected star clicks should save crops into data/champion-star/labeled/<star>",
            ".venv/bin/python scripts/retrain_champion_star.py",
            "or call POST /retrain/champion-star to split, train from the current model, "
            "and replace models/champion-star-classifier.pt when training finishes",
        ],
    }


def retrain_status(process: Optional[subprocess.Popen[bytes]]) -> str:
    if process is None:
        return "idle"

    return "running" if process.poll() is None else "finished"


def read_log_tail(path: Optional[Path], max_bytes: int = 6000) -> str:
    if path is None or not path.exists():
        return ""

    with path.open("rb") as log_file:
        if path.stat().st_size > max_bytes:
            log_file.seek(-max_bytes, 2)
        return log_file.read().decode("utf-8", errors="replace")


def champion_star_retrain_status() -> dict[str, Any]:
    return {
        "status": retrain_status(champion_star_retrain_process),
        "run_name": champion_star_retrain_run_name,
        "log_path": str(champion_star_retrain_log_path)
        if champion_star_retrain_log_path is not None
        else None,
        "log_tail": read_log_tail(champion_star_retrain_log_path),
    }


def ensure_board_crop(image_name: str) -> None:
    board_crop_path = CROPS_DIR / image_name

    if board_crop_path.exists():
        return

    raw_path = RAW_DIR / image_name
    if not raw_path.exists():
        raise FileNotFoundError(
            f"Board crop not found: {board_crop_path}; raw image not found: {raw_path}"
        )

    detection = detect_board(str(RAW_DIR), image_name)
    if detection is None:
        raise ValueError(f"No board detected in raw image: {raw_path}")

    crop_board(str(raw_path), detection, str(board_crop_path))


def start_champion_star_retrain(payload: dict[str, Any]) -> dict[str, Any]:
    global champion_star_retrain_log_path
    global champion_star_retrain_process
    global champion_star_retrain_run_name

    if (
        champion_star_retrain_process is not None
        and champion_star_retrain_process.poll() is None
    ):
        return {
            "started": False,
            "reason": "champion_star_retrain_already_running",
            **champion_star_retrain_status(),
        }

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_name = str(payload.get("name", f"champion-star-api-retrain-{timestamp}"))
    RETRAIN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = RETRAIN_LOG_DIR / f"{run_name}.log"
    command = [
        sys.executable,
        "scripts/retrain_champion_star.py",
        "--name",
        run_name,
        "--epochs",
        str(int(payload.get("epochs", 100))),
        "--imgsz",
        str(int(payload.get("imgsz", 160))),
        "--batch",
        str(int(payload.get("batch", 16))),
        "--device",
        str(payload.get("device", "mps")),
    ]

    log_file = log_path.open("wb")
    champion_star_retrain_process = subprocess.Popen(
        command,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    log_file.close()
    champion_star_retrain_log_path = log_path
    champion_star_retrain_run_name = run_name

    return {
        "started": True,
        "pid": champion_star_retrain_process.pid,
        "command": command,
        **champion_star_retrain_status(),
    }


def build_board_state(query: dict[str, list[str]]) -> dict[str, Any]:
    image_name = first_query_value(query, "image", "image_1.png")
    champion_confidence = float(first_query_value(query, "champion_conf", str(CHAMPION_CONFIDENCE)))
    identity_padding_ratio = float(
        first_query_value(query, "identity_padding", str(CHAMPION_IDENTITY_PADDING_RATIO))
    )
    identity_confidence_threshold = float(
        first_query_value(query, "identity_conf", str(IDENTITY_CONFIDENCE_THRESHOLD))
    )
    ensure_board_crop(image_name)
    (
        current_hex_model,
        current_champion_model,
        current_identity_model,
        current_star_model,
    ) = get_models()
    combine_hex_signals_for_image(
        image_name,
        current_hex_model,
        current_champion_model,
        current_identity_model,
        current_star_model,
        champion_confidence,
        identity_padding_ratio,
        identity_confidence_threshold,
        0.0,
        quiet=True,
    )
    output_path = BOARD_STATE_OUTPUT_DIR / f"{Path(image_name).stem}.json"

    board_state = cast(dict[str, Any], json.loads(output_path.read_text(encoding="utf-8")))
    board_state['hud'] = detect_hud(RAW_DIR / image_name)
    output_path.write_text(json.dumps(board_state, indent=2), encoding='utf-8')
    return board_state


class BoardStateApiHandler(BaseHTTPRequestHandler):
    def send_json(self, status_code: int, body: dict[str, Any]) -> None:
        encoded_body = json.dumps(body, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded_body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(encoded_body)

    def do_OPTIONS(self) -> None:
        self.send_json(200, {"ok": True})

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)

        try:
            if parsed_url.path == "/board-state":
                self.send_json(200, build_board_state(query))
                return

            if parsed_url.path == "/retrain-commands":
                self.send_json(200, retrain_commands())
                return

            if parsed_url.path == "/retrain/champion-star/status":
                self.send_json(200, champion_star_retrain_status())
                return

            self.send_json(
                200,
                {
                    "ok": True,
                    "routes": [
                        "GET /board-state?image=image_388.png",
                        "GET /retrain-commands",
                        "GET /retrain/champion-star/status",
                        "POST /corrections/identity",
                        "POST /corrections/hex-occupancy",
                        "POST /corrections/missing-hex",
                        "POST /retrain/champion-star",
                    ],
                },
            )
        except Exception as error:
            self.send_json(500, {"error": str(error)})

    def do_POST(self) -> None:
        parsed_url = urlparse(self.path)

        try:
            payload = read_json_body(self)

            if parsed_url.path == "/corrections/identity":
                result = save_corrected_name(
                    str(payload["image_name"]),
                    int(payload["box_index"]),
                    str(payload["champion"]),
                    float(payload.get("champion_conf", CHAMPION_CONFIDENCE)),
                    float(payload.get("identity_padding", CHAMPION_IDENTITY_PADDING_RATIO)),
                )
                self.send_json(200, result)
                return

            if parsed_url.path == "/corrections/hex-occupancy":
                result = save_hex_occupancy_correction(
                    str(payload["image_name"]),
                    int(payload["row"]),
                    int(payload["column"]),
                    parse_bool(payload["occupied"]),
                )
                self.send_json(200, result)
                return

            if parsed_url.path == "/corrections/missing-hex":
                self.send_json(200, save_missing_hex_correction(payload))
                return

            if parsed_url.path == "/retrain/champion-star":
                self.send_json(202, start_champion_star_retrain(payload))
                return

            self.send_json(404, {"error": f"Unknown route: {parsed_url.path}"})
        except Exception as error:
            self.send_json(500, {"error": str(error)})

    def log_message(self, format_text: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format_text % args}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    port = int(os.environ.get("PORT", args.port))

    server = ThreadingHTTPServer(
        ("0.0.0.0", port),
        BoardStateApiHandler,
    )

    print(f"Board State API running on port {port}")

    server.serve_forever()


if __name__ == "__main__":
    main()
