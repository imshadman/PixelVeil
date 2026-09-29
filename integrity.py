"""integrity.py - SHA-256 hashing and verification module for steganography payloads.

Computes and verifies SHA-256 cryptographic hashes before embedding and after extraction
to guarantee exact byte-for-byte recovery.
"""

import hashlib
import hmac
from pathlib import Path
from typing import Tuple
from validators import StegoError


class IntegrityVerificationError(StegoError):
    """Raised when the recovered payload SHA-256 hash does not match the original."""
    pass


def compute_sha256(data: bytes) -> bytes:
    """Compute raw 32-byte SHA-256 digest of data bytes.

    Args:
        data: Payload bytes.

    Returns:
        bytes: 32 raw bytes representing the SHA-256 digest.
    """
    return hashlib.sha256(data).digest()


def compute_sha256_hex(data: bytes) -> str:
    """Compute hexadecimal string representation of SHA-256 digest.

    Args:
        data: Payload bytes.

    Returns:
        str: 64-character hexadecimal SHA-256 digest.
    """
    return hashlib.sha256(data).hexdigest()


def compute_file_sha256(file_path: Path | str, chunk_size: int = 65536) -> Tuple[bytes, str]:
    """Compute SHA-256 digest of a file by reading in chunks.

    Supports arbitrary file sizes including 0-byte files.

    Args:
        file_path: Path to the target file.
        chunk_size: Read buffer size in bytes (default 64 KB).

    Returns:
        Tuple[bytes, str]: (raw_32_bytes_digest, hex_string_digest)
    """
    path = Path(file_path)
    hasher = hashlib.sha256()

    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    raw_digest = hasher.digest()
    hex_digest = hasher.hexdigest()
    return raw_digest, hex_digest


def verify_integrity(expected_digest: bytes, actual_digest: bytes) -> bool:
    """Compare expected and actual SHA-256 digests in constant time.

    Args:
        expected_digest: Original 32-byte digest stored in header.
        actual_digest: Computed 32-byte digest from extracted payload.

    Returns:
        bool: True if digests match exactly, False otherwise.
    """
    return hmac.compare_digest(expected_digest, actual_digest)
