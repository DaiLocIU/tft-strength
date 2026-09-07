"""Exercise the byte-oriented HTTP boundary without loading model weights."""

import io
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import inference_api as api


class Handler(api.InferenceHandler):
    def __init__(self, data=b"image", key="test-key", query=""):
        self.path = "/board-state-bytes" + query
        self.headers = {"Content-Length": str(len(data)), "X-Vision-Key": key}
        self.rfile = io.BytesIO(data)
        self.reply = None

    def send_json(self, status, payload):
        self.reply = (status, payload)


class InferenceApiTest(unittest.TestCase):
    @patch.dict(os.environ, {"VISION_SERVICE_KEY": "test-key"})
    @patch.object(api, "infer", return_value={"units": []})
    def test_passes_identical_bytes(self, infer):
        data = bytes([0, 255, 1, 137])
        handler = Handler(data)
        handler.do_POST()
        infer.assert_called_once_with(data, 0.65, 0.08, 0.75)
        self.assertEqual(handler.reply, (200, {"units": []}))
        self.assertFalse(api.INFERENCE_LOCK.locked())

    @patch.dict(os.environ, {"VISION_SERVICE_KEY": "test-key"})
    @patch.object(api, "infer")
    def test_rejects_unauthorized_oversized_and_invalid_parameters(self, infer):
        for handler, status in [
            (Handler(key="wrong"), 401),
            (Handler(query="?champion_conf=nan"), 422),
        ]:
            handler.do_POST()
            self.assertEqual(handler.reply[0], status)
        handler = Handler()
        handler.headers["Content-Length"] = str(api.MAX_IMAGE_BYTES + 1)
        handler.do_POST()
        self.assertEqual(handler.reply[0], 413)
        infer.assert_not_called()

    @patch.dict(os.environ, {"VISION_SERVICE_KEY": "test-key"})
    @patch.object(api, "infer", side_effect=ValueError("No TFT board found"))
    def test_releases_model_lock_after_failure(self, infer):
        handler = Handler()
        handler.do_POST()
        self.assertEqual(handler.reply[0], 422)
        self.assertFalse(api.INFERENCE_LOCK.locked())

    def test_validates_actual_image_format(self):
        image = Image.new("RGB", (8, 8))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        self.assertEqual(api.validated_image(buffer.getvalue()).size, (8, 8))
        with self.assertRaises(ValueError):
            api.validated_image(b"")
        with self.assertRaises(api.UnidentifiedImageError):
            api.validated_image(b"not an image")


class UrlInferenceTest(unittest.TestCase):
    URL = "https://project.supabase.co/storage/v1/object/sign/boards/image.png?token=secret"

    @patch.dict(
        os.environ,
        {"VISION_SERVICE_KEY": "test-key", "VISION_IMAGE_ORIGINS": "https://project.supabase.co"},
    )
    @patch.object(api, "infer_url", return_value={"units": []})
    def test_url_json_contract(self, infer):
        import json

        handler = Handler(json.dumps({"imageUrl": self.URL}).encode())
        handler.path = "/board-state"
        handler.headers["Content-Type"] = "application/json"
        handler.do_POST()
        infer.assert_called_once_with(self.URL, 0.65, 0.08, 0.75)
        self.assertEqual(handler.reply[0], 200)

    @patch.dict(
        os.environ,
        {"VISION_SERVICE_KEY": "test-key", "VISION_IMAGE_ORIGINS": "https://project.supabase.co"},
    )
    @patch.object(api, "infer_url", return_value={"units": []})
    def test_url_json_contract_accepts_chunked_body_without_content_length(self, infer):
        import json

        data = json.dumps({"imageUrl": self.URL}).encode()
        handler = Handler()
        handler.path = "/board-state"
        handler.headers = {
            "X-Vision-Key": "test-key",
            "Content-Type": "application/json",
            "Transfer-Encoding": "chunked",
        }
        handler.rfile = io.BytesIO(
            f"{len(data):X}\r\n".encode() + data + b"\r\n0\r\n\r\n"
        )

        handler.do_POST()

        infer.assert_called_once_with(self.URL, 0.65, 0.08, 0.75)
        self.assertEqual(handler.reply, (200, {"units": []}))

    @patch.dict(os.environ, {"VISION_IMAGE_ORIGINS": "https://project.supabase.co"})
    def test_rejects_untrusted_urls(self):
        for url in [
            None,
            "file:///etc/passwd",
            "http://127.0.0.1/image",
            "https://project.supabase.co.evil.test/image",
            "https://user:pass@project.supabase.co/image",
            "https://project.supabase.co:444/image",
        ]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                api.validate_image_url(url)
        self.assertEqual(api.validate_image_url(self.URL), self.URL)

    @patch.dict(os.environ, {"VISION_IMAGE_ORIGINS": "https://project.supabase.co"})
    def test_original_download_and_cleanup_on_success_and_failure(self):
        class Response(io.BytesIO):
            headers = {}

        original = b"x" * 9_000_000
        seen_paths = []
        real_download = api.download_image

        def record_download(url, path):
            seen_paths.append(path)
            return real_download(url, path)

        with patch.object(api, "build_opener") as opener, patch.object(api, "infer") as infer:
            opener.return_value.open.side_effect = lambda *a, **k: Response(original)
            infer.return_value = {"units": []}
            with patch.object(api, "download_image", side_effect=record_download):
                self.assertEqual(api.infer_url(self.URL), {"units": []})
                self.assertEqual(infer.call_args.args[0], original)
                infer.side_effect = ValueError("No board")
                with self.assertRaises(ValueError):
                    api.infer_url(self.URL)
            self.assertTrue(all(not path.parent.exists() for path in seen_paths))

    @patch.dict(os.environ, {"VISION_IMAGE_ORIGINS": "https://project.supabase.co"})
    def test_oversized_unknown_length_download_and_expired_url(self):
        class Response(io.BytesIO):
            headers = {}

        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory, patch.object(api, "build_opener") as opener:
            opener.return_value.open.return_value = Response(b"x" * (api.MAX_IMAGE_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "10 MB"):
                api.download_image(self.URL, Path(directory) / "image")
            opener.return_value.open.side_effect = api.HTTPError(self.URL, 403, "expired", {}, None)
            with self.assertRaises(ValueError) as error:
                api.download_image(self.URL, Path(directory) / "image")
            self.assertNotIn("token", str(error.exception))

    def test_redirects_are_not_followed(self):
        with self.assertRaises(ValueError):
            api.NoRedirects().redirect_request(None, None, 302, "", {}, "http://127.0.0.1")


if __name__ == "__main__":
    unittest.main()
