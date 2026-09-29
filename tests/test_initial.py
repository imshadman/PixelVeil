"""test_initial.py - Unit tests for validators.py and capacity.py."""

import unittest
from pathlib import Path
import tempfile
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validators import (
    validate_cover_image,
    validate_payload_file,
    sanitize_filename,
    validate_output_path,
    UnsupportedImageError,
    FileValidationError,
)
from capacity import (
    calculate_raw_capacity,
    get_actual_header_size,
    calculate_available_payload,
    check_capacity,
    validate_capacity,
    CapacityExceededError,
)


class TestValidators(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        # Create test images
        self.rgb_png = self.dir_path / "cover_rgb.png"
        Image.new("RGB", (100, 100), color=(255, 0, 0)).save(self.rgb_png, format="PNG")

        self.gray_png = self.dir_path / "gray.png"
        Image.new("L", (100, 100), color=128).save(self.gray_png, format="PNG")

        self.rgba_png = self.dir_path / "cover_rgba.png"
        Image.new("RGBA", (100, 100), color=(255, 0, 0, 255)).save(self.rgba_png, format="PNG")

        self.palette_png = self.dir_path / "palette.png"
        Image.new("P", (100, 100)).save(self.palette_png, format="PNG")

        self.jpeg_img = self.dir_path / "cover.jpg"
        Image.new("RGB", (100, 100), color=(0, 255, 0)).save(self.jpeg_img, format="JPEG")

        # Create test payload files
        self.valid_payload = self.dir_path / "data.txt"
        self.valid_payload.write_text("Hello Stego!")

        self.empty_payload = self.dir_path / "empty.bin"
        self.empty_payload.write_bytes(b"")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_rgb_png_accepted(self):
        img = validate_cover_image(self.rgb_png)
        self.assertEqual(img.format, "PNG")
        self.assertEqual(img.mode, "RGB")
        self.assertEqual(img.size, (100, 100))

    def test_grayscale_rejected(self):
        with self.assertRaises(UnsupportedImageError) as ctx:
            validate_cover_image(self.gray_png)
        self.assertIn("Phase 1 supports RGB PNG images only", str(ctx.exception))

    def test_rgba_rejected(self):
        with self.assertRaises(UnsupportedImageError) as ctx:
            validate_cover_image(self.rgba_png)
        self.assertIn("Phase 1 supports RGB PNG images only", str(ctx.exception))

    def test_palette_rejected(self):
        with self.assertRaises(UnsupportedImageError) as ctx:
            validate_cover_image(self.palette_png)
        self.assertIn("Phase 1 supports RGB PNG images only", str(ctx.exception))

    def test_jpeg_rejected(self):
        with self.assertRaises(UnsupportedImageError) as ctx:
            validate_cover_image(self.jpeg_img)
        self.assertIn("Phase 1 supports RGB PNG images only", str(ctx.exception))

    def test_missing_image_raises_error(self):
        with self.assertRaises(FileValidationError):
            validate_cover_image(self.dir_path / "nonexistent.png")

    def test_payload_validation(self):
        path, size = validate_payload_file(self.valid_payload)
        self.assertEqual(path, self.valid_payload)
        self.assertEqual(size, 12)

    def test_empty_payload_supported(self):
        path, size = validate_payload_file(self.empty_payload)
        self.assertEqual(path, self.empty_payload)
        self.assertEqual(size, 0)

    def test_missing_payload_raises_error(self):
        with self.assertRaises(FileValidationError):
            validate_payload_file(self.dir_path / "nonexistent.txt")

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("../../etc/passwd"), "passwd")
        self.assertEqual(sanitize_filename(r"..\..\Windows\System32\cmd.exe"), "cmd.exe")
        self.assertEqual(sanitize_filename("valid_document.pdf"), "valid_document.pdf")
        self.assertEqual(sanitize_filename(""), "recovered_file.bin")
        self.assertEqual(sanitize_filename("/"), "recovered_file.bin")

    def test_cover_overwrite_protection(self):
        with self.assertRaises(FileValidationError):
            validate_output_path(self.rgb_png, self.rgb_png)


class TestCapacity(unittest.TestCase):
    def test_raw_capacity_calculation(self):
        # 100 x 100 pixels * 3 channels = 30,000 bits = 3,750 bytes
        metrics = calculate_raw_capacity(100, 100)
        self.assertEqual(metrics["width"], 100)
        self.assertEqual(metrics["height"], 100)
        self.assertEqual(metrics["total_pixels"], 10_000)
        self.assertEqual(metrics["capacity_bits"], 30_000)
        self.assertEqual(metrics["capacity_bytes"], 3_750)

    def test_actual_header_size_from_metadata(self):
        # With Version 2 metadata.py, header size for "test.txt" is 78 + 8 = 86 bytes
        size = get_actual_header_size("test.txt")
        self.assertEqual(size, 86)

    def test_available_payload_with_metadata(self):
        # 3,750 bytes raw capacity - 86 bytes actual V2 header = 3,664 bytes
        avail = calculate_available_payload(100, 100, "test.txt")
        self.assertEqual(avail, 3664)

    def test_check_capacity_fits_and_fails(self):
        # Total raw capacity is 3,750 bytes
        # Actual V2 header for "payload.bin" (11 chars) is 78 + 11 = 89 bytes
        # Payload size 3,661 -> Total required = 89 + 3,661 = 3,750 (Fits exactly)
        fits, req, cap = check_capacity(100, 100, 3661, "payload.bin")
        self.assertTrue(fits)
        self.assertEqual(req, 3750)
        self.assertEqual(cap, 3750)

        # Payload size 3,662 -> Total required = 89 + 3,662 = 3,751 (Does not fit)
        fits, req, cap = check_capacity(100, 100, 3662, "payload.bin")
        self.assertFalse(fits)
        self.assertEqual(req, 3751)

    def test_validate_capacity_raises_exception(self):
        with self.assertRaises(CapacityExceededError):
            validate_capacity(100, 100, 5000, "test.bin")


if __name__ == "__main__":
    unittest.main()
