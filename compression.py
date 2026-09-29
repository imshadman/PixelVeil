"""compression.py - Lossless payload compression module for LSB steganography.

Phase 2 Extension:
Provides lossless data compression and decompression using Python's standard zlib library.
"""

import zlib
from validators import StegoError


class CompressionError(StegoError):
    """Raised when compression or decompression fails."""
    pass


def compress_payload(data: bytes, level: int = 6) -> bytes:
    """Compress payload data using zlib DEFLATE algorithm.

    Args:
        data: Uncompressed binary data bytes.
        level: Compression level from 0 (no compression) to 9 (maximum compression).
               Default is 6 (standard balance of speed and compression ratio).

    Returns:
        bytes: Compressed binary data.

    Raises:
        CompressionError: If compression fails.
    """
    try:
        return zlib.compress(data, level=level)
    except Exception as exc:
        raise CompressionError(f"Payload compression failed: {exc}") from exc


def decompress_payload(data: bytes) -> bytes:
    """Decompress zlib-compressed payload data.

    Args:
        data: Compressed binary data bytes.

    Returns:
        bytes: Decompressed original binary data.

    Raises:
        CompressionError: If data is corrupted or cannot be decompressed.
    """
    try:
        return zlib.decompress(data)
    except Exception as exc:
        raise CompressionError(f"Payload decompression failed: {exc}") from exc
