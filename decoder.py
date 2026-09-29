"""decoder.py - Core LSB steganography decoder for RGB PNG images.

Supports:
- Phase 1: Pure LSB steganography extraction with exact byte-for-byte recovery.
- Phase 2: AES-256-GCM authenticated decryption (using complete header as AAD)
           and zlib decompression.
"""

import time
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
from PIL import Image

from validators import (
    validate_cover_image,
    sanitize_filename,
    StegoError,
)
from metadata import (
    unpack_header_prefix,
    unpack_header,
    Header,
    PREFIX_SIZE,
    CorruptedHeaderError,
    InvalidMagicError,
    InvalidVersionError,
    FLAG_COMPRESSED,
    FLAG_ENCRYPTED,
)
from bit_utils import extract_bytes
from integrity import compute_sha256, compute_sha256_hex, verify_integrity, IntegrityVerificationError
from crypto import derive_key, decrypt_payload, DecryptionError
from compression import decompress_payload, CompressionError


class PasswordRequiredError(StegoError):
    """Raised when an encrypted payload is encountered but no password is provided."""
    pass


def decode_file(
    stego_path: Path | str,
    output_dir: Optional[Path | str] = None,
    output_filename: Optional[str] = None,
    password: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract a hidden binary payload from an RGB PNG stego image.

    Pipeline:
    1. Validate stego image format (must be RGB PNG).
    2. Extract initial 10-byte prefix from LSBs.
    3. Determine total header length and extract full serialized header bytes.
    4. Unpack metadata (Version 1 or Version 2).
    5. Extract embedded payload bytes from LSBs.
    6. If encrypted:
       - Require password.
       - Derive AES key using stored salt and PBKDF2-HMAC-SHA256 (100,000 iterations).
       - Decrypt using AES-256-GCM with the complete extracted header as AAD.
         Header authentication applies when AES-GCM encryption is enabled because
         the complete Version-2 header is passed as AES-GCM AAD.
    7. If compressed:
       - Decompress using zlib.
    8. Verify SHA-256 integrity against header digest.
    9. Safely save the recovered file in binary mode ('wb').

    Args:
        stego_path: Path to stego PNG image.
        output_dir: Directory where recovered file will be saved.
        output_filename: Optional custom output filename.
        password: Password string required if the payload is encrypted.

    Returns:
        Dict[str, Any]: Extraction statistics and verification details.

    Raises:
        PasswordRequiredError: If payload is encrypted but no password provided.
        DecryptionError: If password is wrong or header/ciphertext was altered.
        CompressionError: If decompression fails.
        IntegrityVerificationError: If extracted payload SHA-256 does not match original digest.
    """
    start_time = time.perf_counter()

    # Step 1: Validate stego image format
    stego_img = validate_cover_image(stego_path)
    width, height = stego_img.size

    # Step 2: Read pixel channels into 1D flat array
    pixel_array = np.array(stego_img, dtype=np.uint8)
    flat_channels = pixel_array.reshape(-1)
    total_capacity_bytes = len(flat_channels) // 8

    # Step 3: Check if image has enough capacity for header prefix (10 bytes)
    if total_capacity_bytes < PREFIX_SIZE:
        raise CorruptedHeaderError(
            f"Stego image capacity ({total_capacity_bytes} bytes) is too small to contain a header prefix."
        )

    # Step 4: Extract and validate 10-byte prefix
    prefix_bytes = extract_bytes(flat_channels, PREFIX_SIZE, offset_bytes=0)
    version, flags, total_header_len, name_len = unpack_header_prefix(prefix_bytes)

    # Step 5: Extract complete serialized header bytes (needed as AAD for AES-GCM)
    if total_capacity_bytes < total_header_len:
        raise CorruptedHeaderError(
            f"Image capacity ({total_capacity_bytes} bytes) is smaller than required header length ({total_header_len} bytes)."
        )

    full_header_bytes = extract_bytes(flat_channels, total_header_len, offset_bytes=0)
    header = unpack_header(full_header_bytes)

    # Step 6: Validate payload boundary
    total_embedded = header.header_length + header.payload_length
    if total_embedded > total_capacity_bytes:
        raise CorruptedHeaderError(
            f"Image capacity ({total_capacity_bytes} B) is smaller than embedded data "
            f"(header: {header.header_length} B, payload: {header.payload_length} B, total: {total_embedded} B). "
            "The image appears to be truncated or corrupted."
        )

    # Step 7: Extract exact payload bytes
    raw_payload_bytes = extract_bytes(
        flat_channels, header.payload_length, offset_bytes=header.header_length
    )

    # Step 8: Decryption (if encrypted)
    decrypted_bytes = raw_payload_bytes
    if header.is_encrypted:
        if not password:
            raise PasswordRequiredError(
                "Stego payload is encrypted with AES-256-GCM. A password is required to extract."
            )
        key = derive_key(password, header.salt)
        # Authenticate header as AAD
        decrypted_bytes = decrypt_payload(
            ciphertext=raw_payload_bytes,
            key=key,
            nonce=header.nonce,
            associated_data=full_header_bytes,
        )

    # Step 9: Decompression (if compressed)
    if header.is_compressed:
        recovered_original_bytes = decompress_payload(decrypted_bytes)
    else:
        recovered_original_bytes = decrypted_bytes

    # Step 10: Verify cryptographic integrity with original SHA-256
    extracted_digest = compute_sha256(recovered_original_bytes)
    extracted_hex = compute_sha256_hex(recovered_original_bytes)
    expected_hex = header.sha256_digest.hex()

    if not verify_integrity(header.sha256_digest, extracted_digest):
        raise IntegrityVerificationError(
            f"Integrity check FAILED: SHA-256 hash mismatch!\n"
            f"  Expected (Original): {expected_hex}\n"
            f"  Computed (Recovered): {extracted_hex}"
        )

    # Step 11: Determine safe destination path
    dest_dir = Path(output_dir) if output_dir else Path.cwd()
    dest_dir.mkdir(parents=True, exist_ok=True)

    if output_filename:
        safe_name = sanitize_filename(output_filename)
    else:
        safe_name = sanitize_filename(header.filename)

    out_file_path = dest_dir / safe_name

    # Step 12: Write recovered payload in binary mode
    with open(out_file_path, "wb") as f:
        f.write(recovered_original_bytes)

    elapsed_time = time.perf_counter() - start_time

    return {
        "stego_path": str(stego_path),
        "recovered_path": str(out_file_path),
        "filename": safe_name,
        "version": header.version,
        "flags": header.flags,
        "is_compressed": header.is_compressed,
        "is_encrypted": header.is_encrypted,
        "width": width,
        "height": height,
        "total_pixels": width * height,
        "header_size_bytes": header.header_length,
        "payload_size_bytes": len(recovered_original_bytes),
        "embedded_payload_bytes": header.payload_length,
        "expected_sha256": expected_hex,
        "actual_sha256": extracted_hex,
        "integrity_verified": True,
        "decoding_time_sec": elapsed_time,
    }
