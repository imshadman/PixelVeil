"""encoder.py - Core LSB steganography encoder for RGB PNG images.

Supports:
- Phase 1: Pure LSB steganography with exact byte-for-byte recovery.
- Phase 2: Optional zlib compression and AES-256-GCM authenticated encryption.
"""

import time
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
from PIL import Image

from validators import (
    validate_cover_image,
    validate_payload_file,
    validate_output_path,
)
from capacity import calculate_raw_capacity, CapacityExceededError
from metadata import (
    pack_header,
    get_header_size,
    FLAG_NONE,
    FLAG_COMPRESSED,
    FLAG_ENCRYPTED,
    VERSION_2,
)
from bit_utils import bytes_to_bits, embed_lsb
from integrity import compute_sha256, compute_sha256_hex
from compression import compress_payload
from crypto import derive_key, generate_salt, generate_nonce, encrypt_payload


def encode_file(
    cover_path: Path | str,
    payload_path: Path | str,
    output_path: Path | str,
    compress: bool = False,
    password: Optional[str] = None,
) -> Dict[str, Any]:
    """Embed an arbitrary binary file into an RGB PNG cover image using LSB encoding.

    Pipeline:
    1. Read original payload in binary mode ('rb') and compute its SHA-256.
    2. (Optional) Compress payload using zlib.
    3. (Optional) Derive AES-256 key via PBKDF2-HMAC-SHA256 with 16-byte random salt.
    4. Determine exact embedded payload length (including 16-byte GCM tag if encrypted).
    5. Construct complete Version-2 serialized header (78 + N bytes).
    6. (Optional) Encrypt payload using AES-256-GCM with the header as AAD.
       Header authentication applies when AES-GCM encryption is enabled because
       the complete Version-2 header is passed as AES-GCM AAD.
    7. Embed header + embedded_payload into cover image LSBs.
    8. Save modified pixel array as a lossless RGB PNG image.

    Args:
        cover_path: Path to original RGB PNG cover image.
        payload_path: Path to binary payload file to hide.
        output_path: Destination path for stego PNG image.
        compress: True to compress payload with zlib before embedding.
        password: If provided, encrypts payload using AES-256-GCM.

    Returns:
        Dict[str, Any]: Encoding statistics and telemetry.
    """
    start_time = time.perf_counter()

    # Step 1: Validate inputs and cover image
    cover_img = validate_cover_image(cover_path)
    p_path, p_orig_size = validate_payload_file(payload_path)
    out_path = validate_output_path(cover_path, output_path)

    width, height = cover_img.size
    filename = p_path.name

    # Step 2: Read payload bytes in binary mode
    with open(p_path, "rb") as f:
        payload_bytes = f.read()

    # Step 3: Compute original SHA-256
    sha256_digest = compute_sha256(payload_bytes)
    sha256_hex = compute_sha256_hex(payload_bytes)

    # Step 4: Compression (if requested)
    flags = FLAG_NONE
    processed_data = payload_bytes
    if compress:
        processed_data = compress_payload(payload_bytes)
        flags |= FLAG_COMPRESSED

    # Step 5: Encryption setup (if requested)
    salt = b"\x00" * 16
    nonce = b"\x00" * 12
    key = None

    if password:
        flags |= FLAG_ENCRYPTED
        salt = generate_salt()
        nonce = generate_nonce()
        key = derive_key(password, salt)
        # AES-GCM appends a 16-byte authentication tag
        embedded_payload_len = len(processed_data) + 16
    else:
        embedded_payload_len = len(processed_data)

    # Step 6: Construct complete Version-2 header
    header_bytes = pack_header(
        filename=filename,
        payload_length=embedded_payload_len,
        sha256_digest=sha256_digest,
        flags=flags,
        salt=salt,
        nonce=nonce,
        version=VERSION_2,
    )
    header_size = len(header_bytes)

    # Step 7: Check capacity against image
    raw_metrics = calculate_raw_capacity(width, height)
    total_capacity_bytes = raw_metrics["capacity_bytes"]
    total_embed_bytes = header_size + embedded_payload_len

    if total_embed_bytes > total_capacity_bytes:
        raise CapacityExceededError(
            f"Payload does not fit in image ({width}x{height}). "
            f"Processed payload: {embedded_payload_len:,} B, Header: {header_size} B. "
            f"Total required: {total_embed_bytes:,} B. "
            f"Maximum available capacity: {total_capacity_bytes:,} B. "
            f"Shortfall: {total_embed_bytes - total_capacity_bytes:,} B."
        )

    # Step 8: Encryption execution with header as AAD
    if password and key:
        ciphertext = encrypt_payload(
            plaintext=processed_data,
            key=key,
            nonce=nonce,
            associated_data=header_bytes,
        )
        assert len(ciphertext) == embedded_payload_len, "Ciphertext length mismatch"
        final_payload_to_embed = ciphertext
    else:
        final_payload_to_embed = processed_data

    # Step 9: Assemble bitstream and embed into RGB LSBs
    combined_bytes = header_bytes + final_payload_to_embed
    bits_to_embed = bytes_to_bits(combined_bytes)

    pixel_array = np.array(cover_img, dtype=np.uint8)
    flat_channels = pixel_array.reshape(-1)

    modified_channels = embed_lsb(flat_channels, bits_to_embed)
    stego_array = modified_channels.reshape(pixel_array.shape)

    # Step 10: Save stego image losslessly
    stego_image = Image.fromarray(stego_array)
    stego_image.save(out_path, format="PNG")

    elapsed_time = time.perf_counter() - start_time

    return {
        "cover_path": str(cover_path),
        "output_path": str(out_path),
        "payload_filename": filename,
        "width": width,
        "height": height,
        "total_pixels": width * height,
        "raw_capacity_bytes": total_capacity_bytes,
        "header_size_bytes": header_size,
        "original_payload_bytes": p_orig_size,
        "embedded_payload_bytes": embedded_payload_len,
        "total_embedded_bytes": total_embed_bytes,
        "remaining_capacity_bytes": total_capacity_bytes - total_embed_bytes,
        "payload_sha256": sha256_hex,
        "is_compressed": bool(flags & FLAG_COMPRESSED),
        "is_encrypted": bool(flags & FLAG_ENCRYPTED),
        "flags": flags,
        "encoding_time_sec": elapsed_time,
    }
