"""test_phase1.py - Comprehensive test suite for Phase 1 LSB Steganography.

Covers all 12 mandatory requirements:
 1. TXT payload
 2. PDF payload
 3. JPG payload
 4. ZIP payload
 5. Random binary payload
 6. Empty file (0 bytes)
 7. Payload too large (rejection before image modification)
 8. Normal PNG without hidden payload (rejects invalid magic)
 9. Grayscale image rejection
10. RGBA image rejection
11. Filename containing spaces
12. SHA-256 integrity verification (matching & tamper detection)
"""

import os
import io
import zipfile
import tempfile
import unittest
from pathlib import Path
from PIL import Image
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from encoder import encode_file
from decoder import decode_file
from integrity import compute_file_sha256, IntegrityVerificationError
from metadata import InvalidMagicError
from capacity import CapacityExceededError
from validators import UnsupportedImageError


class TestPhase1Steganography(unittest.TestCase):
    """Test suite exercising the complete Phase 1 LSB steganography system."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.td = Path(self.temp_dir.name)

        # Standard 300x300 RGB cover image (Capacity = 300 * 300 * 3 // 8 = 33,750 bytes)
        self.cover_path = self.td / "cover.png"
        img = Image.new("RGB", (300, 300), color=(64, 128, 192))
        img.save(self.cover_path, format="PNG")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _run_encode_decode_cycle(self, payload_path: Path, expected_name: str | None = None) -> Path:
        """Helper to run encode -> decode -> verify SHA256 and byte-for-byte identity."""
        stego_path = self.td / f"stego_{payload_path.stem}.png"
        rec_dir = self.td / f"rec_{payload_path.stem}"

        # 1. Encode
        enc_stats = encode_file(self.cover_path, payload_path, stego_path)
        self.assertTrue(stego_path.exists())
        self.assertGreater(enc_stats["encoding_time_sec"], 0)

        # 2. Decode
        dec_stats = decode_file(stego_path, output_dir=rec_dir)
        target_name = expected_name if expected_name else payload_path.name
        recovered_file = rec_dir / target_name

        self.assertTrue(recovered_file.exists(), f"Recovered file {recovered_file} missing")
        self.assertTrue(dec_stats["integrity_verified"])

        # 3. Exact byte-for-byte comparison
        orig_bytes = payload_path.read_bytes()
        rec_bytes = recovered_file.read_bytes()
        self.assertEqual(orig_bytes, rec_bytes, "Recovered bytes do not match original bytes!")

        # 4. SHA-256 verification
        _, orig_sha = compute_file_sha256(payload_path)
        _, rec_sha = compute_file_sha256(recovered_file)
        self.assertEqual(orig_sha, rec_sha, "Recovered SHA-256 does not match original!")
        self.assertEqual(dec_stats["actual_sha256"], orig_sha)

        return recovered_file

    def test_01_txt_payload(self):
        """Test 1: Plain text file embedding and extraction."""
        p = self.td / "notes.txt"
        p.write_text("Least Significant Bit (LSB) Steganography College Mini-Project Phase 1 Test.")
        self._run_encode_decode_cycle(p)

    def test_02_pdf_payload(self):
        """Test 2: PDF document embedding and extraction."""
        p = self.td / "document.pdf"
        # Standard valid minimal PDF structure
        pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
            b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >> endobj\n"
            b"xref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n"
            b"trailer << /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF"
        )
        p.write_bytes(pdf_bytes)
        self._run_encode_decode_cycle(p)

    def test_03_jpg_payload(self):
        """Test 3: JPEG image binary payload embedding and extraction."""
        p = self.td / "picture.jpg"
        jpg_img = Image.new("RGB", (40, 40), color=(255, 120, 0))
        jpg_img.save(p, format="JPEG")
        self._run_encode_decode_cycle(p)

    def test_04_zip_payload(self):
        """Test 4: ZIP compressed archive embedding and extraction."""
        p = self.td / "archive.zip"
        with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("hello.txt", "Compressed file contents inside ZIP archive")
            zf.writestr("subfolder/data.bin", b"\x00\x01\x02\x03\x04\x05")
        self._run_encode_decode_cycle(p)

    def test_05_random_binary_payload(self):
        """Test 5: Arbitrary raw random binary bytes."""
        p = self.td / "random.bin"
        p.write_bytes(os.urandom(4096))
        self._run_encode_decode_cycle(p)

    def test_06_empty_file_payload(self):
        """Test 6: Zero-byte empty payload file."""
        p = self.td / "empty.dat"
        p.write_bytes(b"")
        self._run_encode_decode_cycle(p)

    def test_07_payload_too_large(self):
        """Test 7: Payload exceeding capacity is rejected before image modification."""
        p = self.td / "huge.dat"
        # 300x300 RGB capacity = 33,750 bytes. We create 40,000 bytes.
        p.write_bytes(b"X" * 40000)
        stego_path = self.td / "should_not_exist.png"

        with self.assertRaises(CapacityExceededError):
            encode_file(self.cover_path, p, stego_path)

        self.assertFalse(stego_path.exists())

    def test_08_normal_png_without_hidden_payload(self):
        """Test 8: Decoding an unmodified RGB PNG fails gracefully with InvalidMagicError."""
        pure_cover = self.td / "pure_unmodified.png"
        Image.new("RGB", (100, 100), color=(10, 20, 30)).save(pure_cover, format="PNG")

        with self.assertRaises(InvalidMagicError):
            decode_file(pure_cover, output_dir=self.td / "rec")

    def test_09_grayscale_image_rejection(self):
        """Test 9: Grayscale image format rejection."""
        gray_path = self.td / "gray.png"
        Image.new("L", (100, 100), color=128).save(gray_path, format="PNG")
        p = self.td / "dummy.txt"
        p.write_text("hello")

        with self.assertRaises(UnsupportedImageError) as ctx:
            encode_file(gray_path, p, self.td / "out.png")
        self.assertIn("Phase 1 supports RGB PNG images only", str(ctx.exception))

    def test_10_rgba_image_rejection(self):
        """Test 10: RGBA image format rejection."""
        rgba_path = self.td / "rgba.png"
        Image.new("RGBA", (100, 100), color=(255, 0, 0, 255)).save(rgba_path, format="PNG")
        p = self.td / "dummy.txt"
        p.write_text("hello")

        with self.assertRaises(UnsupportedImageError) as ctx:
            encode_file(rgba_path, p, self.td / "out.png")
        self.assertIn("Phase 1 supports RGB PNG images only", str(ctx.exception))

    def test_11_filename_containing_spaces(self):
        """Test 11: Preserving and safely recovering filename with spaces."""
        p = self.td / "my secret project document 2026.txt"
        p.write_text("Secret content with spaces in filename")
        self._run_encode_decode_cycle(p, expected_name="my secret project document 2026.txt")

    def test_12_sha256_verification_and_tamper_detection(self):
        """Test 12: SHA-256 verification and failure when stego bits are tampered."""
        p = self.td / "integrity_test.txt"
        p.write_text("High security data requiring integrity verification.")
        stego_path = self.td / "stego_integrity.png"

        # Encode
        encode_file(self.cover_path, p, stego_path)

        # Tamper with stego image pixel bits in the payload area
        stego_img = Image.open(stego_path)
        arr = np.array(stego_img)
        # Flip LSB of a channel in the payload region (pixel index 260 is well past the 96-byte header)
        arr[0, 260, 0] ^= 1
        tampered_path = self.td / "tampered.png"
        Image.fromarray(arr).save(tampered_path, format="PNG")

        # Decoding tampered stego image must fail SHA-256 integrity verification
        with self.assertRaises(IntegrityVerificationError):
            decode_file(tampered_path, output_dir=self.td / "tampered_rec")


if __name__ == "__main__":
    unittest.main()
