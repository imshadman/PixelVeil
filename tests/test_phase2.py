"""test_phase2.py - Test suite for Phase 2: Compression + Encryption.

Covers the mandatory Phase 2 test cases:
1. Compression only (zlib)
2. Encryption only (AES-256-GCM + PBKDF2)
3. Compression + Encryption combined
4. Wrong password / decryption failure
5. Already-compressed files (e.g. ZIP/PNG payload)
6. Exact byte-for-byte recovery and SHA-256 match
7. Header tampering detection via AES-GCM AAD
8. Version 1 legacy backward compatibility decoding
"""

import os
import zipfile
import tempfile
import unittest
from pathlib import Path
from PIL import Image
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from encoder import encode_file
from decoder import decode_file, PasswordRequiredError
from crypto import DecryptionError
from integrity import compute_file_sha256
from metadata import pack_header, VERSION_1
from bit_utils import bytes_to_bits, embed_lsb


class TestPhase2Steganography(unittest.TestCase):
    """Test suite covering Phase 2 compression, encryption, and backward compatibility."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.td = Path(self.temp_dir.name)

        # Standard 300x300 RGB cover image (Capacity = 300 * 300 * 3 // 8 = 33,750 bytes)
        self.cover_path = self.td / "cover.png"
        img = Image.new("RGB", (300, 300), color=(70, 130, 180))
        img.save(self.cover_path, format="PNG")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _verify_cycle(
        self,
        payload_path: Path,
        compress: bool = False,
        password: str | None = None,
        decode_password: str | None = None,
        tag: str = "run",
    ) -> Path:
        stego_path = self.td / f"stego_{tag}.png"
        rec_dir = self.td / f"rec_{tag}"

        enc_stats = encode_file(
            cover_path=self.cover_path,
            payload_path=payload_path,
            output_path=stego_path,
            compress=compress,
            password=password,
        )
        self.assertTrue(stego_path.exists())

        dec_stats = decode_file(
            stego_path=stego_path,
            output_dir=rec_dir,
            password=decode_password if decode_password is not None else password,
        )

        recovered_file = rec_dir / payload_path.name
        self.assertTrue(recovered_file.exists())
        self.assertTrue(dec_stats["integrity_verified"])

        # Exact byte-for-byte identity
        self.assertEqual(payload_path.read_bytes(), recovered_file.read_bytes())

        # SHA-256 match
        _, orig_sha = compute_file_sha256(payload_path)
        _, rec_sha = compute_file_sha256(recovered_file)
        self.assertEqual(orig_sha, rec_sha)
        self.assertEqual(dec_stats["actual_sha256"], orig_sha)

        return recovered_file

    def test_01_compression_only(self):
        """Test 1: Compress only with zlib, verify smaller stream and exact recovery."""
        payload = self.td / "repetitive_text.txt"
        # Highly compressible repetitive text
        payload.write_text("Antigravity Steganography Mini-Project! " * 200)

        stego_path = self.td / "stego_comp.png"
        rec_dir = self.td / "rec_comp"

        enc_stats = encode_file(
            cover_path=self.cover_path,
            payload_path=payload,
            output_path=stego_path,
            compress=True,
            password=None,
        )
        self.assertTrue(enc_stats["is_compressed"])
        self.assertFalse(enc_stats["is_encrypted"])
        self.assertLess(enc_stats["embedded_payload_bytes"], enc_stats["original_payload_bytes"])

        dec_stats = decode_file(stego_path, output_dir=rec_dir)
        rec_file = rec_dir / payload.name
        self.assertEqual(payload.read_bytes(), rec_file.read_bytes())

    def test_02_encryption_only(self):
        """Test 2: Encrypt only with AES-256-GCM, verify exact recovery."""
        payload = self.td / "secret_document.txt"
        payload.write_text("Classified payload requiring AES-256-GCM encryption.")

        stego_path = self.td / "stego_enc.png"
        rec_dir = self.td / "rec_enc"

        enc_stats = encode_file(
            cover_path=self.cover_path,
            payload_path=payload,
            output_path=stego_path,
            compress=False,
            password="StrongPassword2026!",
        )
        self.assertFalse(enc_stats["is_compressed"])
        self.assertTrue(enc_stats["is_encrypted"])
        # Embedded payload size is original + 16-byte GCM tag
        self.assertEqual(
            enc_stats["embedded_payload_bytes"],
            enc_stats["original_payload_bytes"] + 16,
        )

        dec_stats = decode_file(
            stego_path, output_dir=rec_dir, password="StrongPassword2026!"
        )
        rec_file = rec_dir / payload.name
        self.assertEqual(payload.read_bytes(), rec_file.read_bytes())

    def test_03_compression_and_encryption(self):
        """Test 3: Compression + Encryption combined."""
        payload = self.td / "data_combined.json"
        payload.write_text('{"project": "IVP", "phase": 2, "status": "active"} ' * 50)

        self._verify_cycle(
            payload_path=payload,
            compress=True,
            password="CombinedSecretPassphrase#1",
            tag="both",
        )

    def test_04_wrong_password_and_missing_password(self):
        """Test 4: Decryption fails with wrong password or missing password."""
        payload = self.td / "locked.txt"
        payload.write_text("Confidential information.")
        stego_path = self.td / "stego_locked.png"

        encode_file(
            cover_path=self.cover_path,
            payload_path=payload,
            output_path=stego_path,
            compress=True,
            password="CorrectPassword123",
        )

        # Missing password raises PasswordRequiredError
        with self.assertRaises(PasswordRequiredError):
            decode_file(stego_path, output_dir=self.td / "rec_fail", password=None)

        # Wrong password raises DecryptionError (AES-GCM tag verification failure)
        with self.assertRaises(DecryptionError):
            decode_file(stego_path, output_dir=self.td / "rec_fail", password="IncorrectPassword!")

    def test_05_already_compressed_files(self):
        """Test 5: Embedding already-compressed files (ZIP archive)."""
        payload = self.td / "archive.zip"
        with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("test1.txt", "Content 1 inside zip archive")
            zf.writestr("nested/test2.bin", os.urandom(512))

        self._verify_cycle(
            payload_path=payload,
            compress=True,  # Test zlib on already-deflated content
            password="ZipPassword!",
            tag="already_compressed",
        )

    def test_06_exact_recovery_random_binary(self):
        """Test 6: Exact byte-for-byte recovery on arbitrary random binary data."""
        payload = self.td / "random.dat"
        payload.write_bytes(os.urandom(2048))

        self._verify_cycle(
            payload_path=payload,
            compress=True,
            password="RandomBytesSecretKey",
            tag="random_exact",
        )

    def test_07_header_tampering_caught_by_gcm_aad(self):
        """Test 7: Header tampering is caught because header is used as AES-GCM AAD."""
        payload = self.td / "aad_test.txt"
        payload.write_text("Data bound to header metadata via AAD.")
        stego_path = self.td / "stego_aad.png"

        encode_file(
            cover_path=self.cover_path,
            payload_path=payload,
            output_path=stego_path,
            compress=False,
            password="AADVerificationPassword",
        )

        # Tamper with a bit inside the 16-byte salt (pixel index 95, byte offset ~35)
        # This keeps the prefix and payload length intact, but alters the header AAD bytes
        stego_img = Image.open(stego_path)
        arr = np.array(stego_img)
        arr[0, 95, 0] ^= 1  # Flip LSB inside salt field
        tampered_path = self.td / "stego_tampered_header.png"
        Image.fromarray(arr).save(tampered_path, format="PNG")

        # Even with correct password, GCM tag check fails because AAD was altered
        with self.assertRaises(DecryptionError):
            decode_file(
                tampered_path,
                output_dir=self.td / "rec_tampered_hdr",
                password="AADVerificationPassword",
            )

    def test_08_version_1_backward_compatibility(self):
        """Test 8: Ensure decoder cleanly decodes legacy Version 1 stego images."""
        payload = self.td / "v1_legacy.txt"
        payload_data = b"Legacy Version 1 payload without Phase 2 fields."
        payload.write_bytes(payload_data)

        import hashlib
        digest = hashlib.sha256(payload_data).digest()
        # Pack legacy Version 1 header (50 bytes base)
        v1_header = pack_header(
            filename=payload.name,
            payload_length=len(payload_data),
            sha256_digest=digest,
            version=VERSION_1,
        )

        # Manually embed V1 header + payload into cover
        combined = v1_header + payload_data
        bits = bytes_to_bits(combined)
        img = Image.open(self.cover_path)
        arr = np.array(img)
        flat = arr.reshape(-1)
        modified = embed_lsb(flat, bits)
        stego_v1_path = self.td / "stego_v1.png"
        Image.fromarray(modified.reshape(arr.shape)).save(stego_v1_path, format="PNG")

        # Decode using Phase 2 decoder
        dec_stats = decode_file(stego_v1_path, output_dir=self.td / "rec_v1")
        self.assertEqual(dec_stats["version"], 1)
        self.assertFalse(dec_stats["is_compressed"])
        self.assertFalse(dec_stats["is_encrypted"])
        rec_file = self.td / "rec_v1" / payload.name
        self.assertEqual(rec_file.read_bytes(), payload_data)


if __name__ == "__main__":
    unittest.main()
