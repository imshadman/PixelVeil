"""test_api.py - Integration tests for the FastAPI wrapper.

Verifies:
1. Health endpoint
2. Inspect cover image endpoint
3. Headroom analysis endpoint
4. Full encode -> decode cycle with compression & encryption
5. Wrong password handling
6. Image quality analysis endpoint (MSE, PSNR, SSIM)
7. Experiments JSON endpoint
"""

import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image
import io

import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from api.app import app

client = TestClient(app)


class TestSteganographyAPI(unittest.TestCase):
    """Integration test suite for FastAPI steganography endpoints."""

    def setUp(self):
        # Create an in-memory 100x100 RGB PNG
        img = Image.new("RGB", (100, 100), color=(100, 150, 200))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        self.cover_png_bytes = buf.getvalue()

        # Non-RGB image (RGBA)
        img_rgba = Image.new("RGBA", (100, 100), color=(100, 150, 200, 255))
        buf_rgba = io.BytesIO()
        img_rgba.save(buf_rgba, format="PNG")
        self.rgba_png_bytes = buf_rgba.getvalue()

    def test_01_health_check(self):
        res = client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")

    def test_02_inspect_cover(self):
        files = {"cover": ("cover.png", self.cover_png_bytes, "image/png")}
        res = client.post("/api/inspect-cover", files=files)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["width"], 100)
        self.assertEqual(data["height"], 100)
        self.assertEqual(data["mode"], "RGB")
        self.assertEqual(data["raw_capacity_bytes"], 3750)

    def test_03_reject_non_rgb(self):
        files = {"cover": ("cover_rgba.png", self.rgba_png_bytes, "image/png")}
        res = client.post("/api/inspect-cover", files=files)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Phase 1 supports RGB PNG images only", res.json()["detail"])

    def test_04_check_headroom(self):
        files = {
            "cover": ("cover.png", self.cover_png_bytes, "image/png"),
            "payload": ("test.txt", b"Hello API Payload!", "text/plain"),
        }
        res = client.post("/api/check-headroom", files=files)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["fits"])
        self.assertEqual(data["capacity_bytes"], 3750)

    def test_05_encode_decode_cycle_with_compression_and_encryption(self):
        payload_content = b"Secret payload data for API integration test."
        files = {
            "cover": ("cover.png", self.cover_png_bytes, "image/png"),
            "payload": ("document.txt", payload_content, "text/plain"),
        }
        form_data = {
            "compress": "true",
            "password": "ApiSecretPassword2026!",
        }
        # 1. Encode
        enc_res = client.post("/api/encode", files=files, data=form_data)
        self.assertEqual(enc_res.status_code, 200)
        stego_png_bytes = enc_res.content

        # 2. Probe stego
        probe_res = client.post("/api/probe-stego", files={"stego": ("stego.png", stego_png_bytes, "image/png")})
        self.assertEqual(probe_res.status_code, 200)
        probe_data = probe_res.json()
        self.assertTrue(probe_data["is_compressed"])
        self.assertTrue(probe_data["is_encrypted"])
        self.assertEqual(probe_data["filename"], "document.txt")

        # 3. Decode with wrong password -> 403
        bad_decode = client.post(
            "/api/decode",
            files={"stego": ("stego.png", stego_png_bytes, "image/png")},
            data={"password": "WrongPassword!"},
        )
        self.assertEqual(bad_decode.status_code, 403)

        # 4. Decode with correct password -> 200 and exact bytes
        good_decode = client.post(
            "/api/decode",
            files={"stego": ("stego.png", stego_png_bytes, "image/png")},
            data={"password": "ApiSecretPassword2026!"},
        )
        self.assertEqual(good_decode.status_code, 200)
        self.assertEqual(good_decode.content, payload_content)
        self.assertEqual(good_decode.headers["X-Integrity-Verified"], "True")

    def test_06_analyze_endpoint(self):
        # Stego with slight change
        files = {
            "cover": ("cover.png", self.cover_png_bytes, "image/png"),
            "payload": ("data.txt", b"Small test", "text/plain"),
        }
        enc_res = client.post("/api/encode", files=files)
        stego_bytes = enc_res.content

        analyze_res = client.post(
            "/api/analyze",
            files={
                "cover": ("cover.png", self.cover_png_bytes, "image/png"),
                "stego": ("stego.png", stego_bytes, "image/png"),
            },
        )
        self.assertEqual(analyze_res.status_code, 200)
        data = analyze_res.json()
        self.assertIn("mse", data)
        self.assertIn("psnr_db", data)
        self.assertIn("ssim", data)
        self.assertGreater(data["psnr_db"], 50.0)

    def test_07_experiments_endpoint(self):
        res = client.get("/api/experiments")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("results", data)
        self.assertIn("plots", data)
        self.assertGreaterEqual(len(data["results"]), 12)


if __name__ == "__main__":
    unittest.main()
