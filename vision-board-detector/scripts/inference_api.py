"""Production HTTP boundary: signed image URL in, board JSON out; no training routes."""

from __future__ import annotations

import hmac
import io
import json
import math
import os
import sys
import threading
import time
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 10_000_000
MAX_JSON_BYTES = 16_384
DOWNLOAD_TIMEOUT = 30
MAX_IMAGE_PIXELS = 20_000_000
INFERENCE_LOCK = threading.Lock()
MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
# Ultralytics patches Image.open to install HEIF support on decoding failures.
# Retain Pillow's decoder: this API only accepts PNG/JPEG/WebP and must never
# try to install packages while handling an invalid upload.
OPEN_IMAGE = getattr(sys.modules.get("ultralytics.utils.patches"), "_image_open", Image.open)


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Image redirects are not allowed")


def validate_image_url(value: object) -> str:
    if not isinstance(value, str) or len(value) > 8192:
        raise ValueError("imageUrl must be a signed HTTPS URL")
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
        or parsed.port not in (None, 443)
    ):
        raise ValueError("imageUrl must be a signed HTTPS URL")
    # An exact configured origin, not a wildcard or user-supplied hostname.
    allowed = {
        entry.strip().rstrip("/")
        for entry in os.getenv("VISION_IMAGE_ORIGINS", "").split(",")
        if entry.strip()
    }
    if f"https://{parsed.netloc}" not in allowed:
        raise ValueError("Image origin is not allowed")
    return value


def download_image(url: str, destination: Path) -> None:
    url = validate_image_url(url)
    opener = build_opener(ProxyHandler({}), NoRedirects())
    started = time.monotonic()
    try:
        with opener.open(
            Request(url, headers={"Accept": "image/*"}), timeout=DOWNLOAD_TIMEOUT
        ) as response:
            length = response.headers.get("Content-Length")
            if length is not None and not 0 < int(length) <= MAX_IMAGE_BYTES:
                raise ValueError("Screenshot must be at most 10 MB")
            total = 0
            with destination.open("wb") as output:
                while True:
                    if time.monotonic() - started > DOWNLOAD_TIMEOUT:
                        raise ValueError("Image download timed out")
                    chunk = response.read1(min(64 * 1024, MAX_IMAGE_BYTES + 1 - total))
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_IMAGE_BYTES:
                        raise ValueError("Screenshot must be at most 10 MB")
                    output.write(chunk)
            if total == 0 or (length is not None and total != int(length)):
                raise ValueError("Image download was empty or incomplete")
    except (HTTPError, URLError, TimeoutError, OSError):
        # Signed URLs are credentials: never include them in errors or logs.
        raise ValueError("Image download failed or URL expired; request a new URL") from None


def infer_url(url: str, *params) -> dict:
    with TemporaryDirectory(prefix="tft-download-") as directory:
        path = Path(directory) / "original"
        download_image(url, path)
        return infer(path.read_bytes(), *params)


def validated_image(data: bytes) -> Image.Image:
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Use a PNG, JPEG, or WebP image up to 10 MB")
    with OPEN_IMAGE(io.BytesIO(data)) as source:
        if source.format not in {"PNG", "JPEG", "WEBP"}:
            raise ValueError("Use a PNG, JPEG, or WebP image")
        if source.width * source.height > MAX_IMAGE_PIXELS:
            raise ValueError("Screenshot exceeds 20 megapixels")
        return source.convert("RGB")


@lru_cache(maxsize=1)
def get_models():
    import torch
    from ultralytics import YOLO

    torch.set_num_threads(1)
    return tuple(
        YOLO(MODEL_DIR / name)
        for name in (
            "board-detector.pt",
            "hex-occupancy-classifier.pt",
            "champion-detector.pt",
            "champion-identity-classifier.pt",
            "champion-star-classifier.pt",
        )
    )


def infer(
    data: bytes,
    champion_conf: float = 0.65,
    identity_padding: float = 0.08,
    identity_conf: float = 0.75,
) -> dict:
    import _bootstrap  # noqa: F401
    from predict_hex_occupancy import predict_board_hex_occupancy

    from board_detector.board_geometry import create_board_hex_cells, make_tuning_for_image
    from board_detector.board_state_pipeline import combine_predictions, create_board_state
    from board_detector.champion_hex_evidence import get_champion_hex_evidence
    from board_detector.hud_ocr import detect_hud
    from board_detector.model_adapters import detect_board_box

    image = validated_image(data)
    detector, occupancy, champion, identity, star = get_models()
    # Every request owns its scratch files. No original, crop or output persists.
    with TemporaryDirectory(prefix="tft-inference-") as directory:
        original = Path(directory) / "original.png"
        crop = Path(directory) / "board.png"
        image.save(original)
        box = detect_board_box(original, detector)
        if box is None:
            raise ValueError("No TFT board found. Upload an unobstructed screenshot.")
        image.crop(tuple(int(box[key]) for key in ("x1", "y1", "x2", "y2"))).save(crop)
        hexes = sorted(
            create_board_hex_cells(str(crop), make_tuning_for_image(crop.name)),
            key=lambda cell: (cell["row"], cell["column"]),
        )
        occupied = predict_board_hex_occupancy(
            crop, MODEL_DIR / "hex-occupancy-classifier.pt", occupancy
        )
        evidence = get_champion_hex_evidence(
            crop, champion, identity, star, champion_conf, identity_padding, 0.0, hexes, occupied
        )
        signals = combine_predictions(
            occupied,
            *[
                evidence[key]
                for key in (
                    "confidences_by_hex",
                    "champion_names_by_hex",
                    "identity_confidences_by_hex",
                    "identity_candidates_by_hex",
                    "star_labels_by_hex",
                    "star_confidences_by_hex",
                    "star_candidates_by_hex",
                    "suppressed_occupancy_keys",
                )
            ],
            identity_conf,
        )
        state = create_board_state(
            "upload",
            signals,
            {
                "champion_confidence": champion_conf,
                "identity_padding_ratio": identity_padding,
                "identity_confidence_threshold": identity_conf,
            },
        )
        state["hud"] = detect_hud(original)
        return state


class InferenceHandler(BaseHTTPRequestHandler):
    def send_json(self, status: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.send_json(
            200 if self.path == "/health" else 404,
            {"ok": True} if self.path == "/health" else {"error": "Not found"},
        )

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path not in {"/board-state", "/board-state-bytes"}:
            self.send_json(404, {"error": "Not found"})
            return
        key = os.getenv("VISION_SERVICE_KEY")
        if not key or not hmac.compare_digest(self.headers.get("X-Vision-Key", ""), key):
            self.send_json(401, {"error": "Invalid service key"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            is_url = parsed.path == "/board-state"
            limit = MAX_JSON_BYTES if is_url else 4_000_000
            if not 0 < length <= limit:
                self.send_json(413, {"error": "Request body is too large or empty"})
                return
            if is_url and self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                self.send_json(415, {"error": "Send application/json with imageUrl"})
                return
            query = parse_qs(parsed.query)
            params = [
                float(query.get(name, [default])[0])
                for name, default in (
                    ("champion_conf", ".65"),
                    ("identity_padding", ".08"),
                    ("identity_conf", ".75"),
                )
            ]
            if any(not math.isfinite(value) or not 0 <= value <= 1 for value in params):
                raise ValueError("Detection parameters must be between 0 and 1")
            if not INFERENCE_LOCK.acquire(blocking=False):
                self.send_json(503, {"error": "Detector busy. Please retry shortly."})
                return
            try:
                data = self.rfile.read(length)
                if len(data) != length:
                    raise ValueError("Incomplete image upload")
                if is_url:
                    try:
                        payload = json.loads(data)
                    except (ValueError, UnicodeDecodeError):
                        raise ValueError("Invalid JSON request") from None
                    if not isinstance(payload, dict):
                        raise ValueError("Send an object with imageUrl")
                    result = infer_url(validate_image_url(payload.get("imageUrl")), *params)
                else:
                    # Temporary compatibility for the local upload flow.
                    result = infer(data, *params)
            finally:
                INFERENCE_LOCK.release()
            self.send_json(200, result)
        except (ValueError, UnidentifiedImageError, Image.DecompressionBombError) as error:
            self.send_json(422, {"error": str(error)})
        except Exception:
            # Do not log exceptions that could contain signed URL tokens.
            self.send_json(500, {"error": "Detection failed. Please retry."})


if __name__ == "__main__":
    if not os.getenv("VISION_SERVICE_KEY"):
        raise SystemExit("VISION_SERVICE_KEY is required")
    server = ThreadingHTTPServer(
        (os.getenv("HOST", "127.0.0.1"), int(os.getenv("PORT", "8095"))), InferenceHandler
    )
    print(f"Inference API listening on {server.server_address}", flush=True)
    server.serve_forever()
