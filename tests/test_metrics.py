"""test_metrics.py - Unit tests for metrics.py: MSE, PSNR, and SSIM."""

import unittest
import numpy as np
from pathlib import Path
import tempfile
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from metrics import calculate_mse, calculate_psnr, calculate_ssim, evaluate_image_quality


class TestMetrics(unittest.TestCase):
    """Unit tests verifying MSE, PSNR, and SSIM mathematical properties."""

    def test_identical_images(self):
        arr = np.random.randint(0, 256, (120, 120, 3), dtype=np.uint8)
        self.assertEqual(calculate_mse(arr, arr), 0.0)
        self.assertEqual(calculate_psnr(arr, arr), float("inf"))
        self.assertAlmostEqual(calculate_ssim(arr, arr), 1.0, places=5)

    def test_known_mse_and_psnr(self):
        # 10x10 array where every pixel differs by exactly 1 in all channels
        a = np.zeros((10, 10, 3), dtype=np.uint8)
        b = np.ones((10, 10, 3), dtype=np.uint8)
        # diff is 1, diff^2 is 1, mean is 1.0
        mse = calculate_mse(a, b)
        self.assertAlmostEqual(mse, 1.0)
        # PSNR = 10 * log10(255^2 / 1) = 20 * log10(255) = ~48.1308 dB
        psnr = calculate_psnr(a, b)
        self.assertAlmostEqual(psnr, 48.1308036, places=4)

    def test_ssim_range_and_sensitivity(self):
        # Test SSIM is <= 1.0 and drops gracefully when noise is added
        a = np.random.randint(50, 200, (100, 100, 3), dtype=np.uint8)
        b = a.copy()
        # Add slight LSB noise
        b ^= 1
        ssim = calculate_ssim(a, b)
        self.assertTrue(0.0 <= ssim <= 1.0)
        self.assertGreater(ssim, 0.95)

    def test_evaluate_image_quality_files(self):
        with tempfile.TemporaryDirectory() as td:
            p_cover = Path(td) / "cover.png"
            p_stego = Path(td) / "stego.png"

            Image.new("RGB", (60, 60), color=(100, 150, 200)).save(p_cover, format="PNG")
            img_stego = Image.new("RGB", (60, 60), color=(101, 150, 200))
            img_stego.save(p_stego, format="PNG")

            res = evaluate_image_quality(p_cover, p_stego)
            self.assertIn("mse", res)
            self.assertIn("psnr_db", res)
            self.assertIn("ssim", res)
            self.assertGreater(res["psnr_db"], 40.0)
            self.assertGreater(res["ssim"], 0.99)


if __name__ == "__main__":
    unittest.main()
