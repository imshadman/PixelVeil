"""bit_utils.py - Low-level bitwise operations and LSB manipulation for steganography.

Provides bitwise/NumPy routines for converting between byte buffers and bit arrays,
and embedding / extracting bits into / from carrier pixel channel values using
LSB replacement: new_value = (old_value & 0xFE) | bit
"""

import numpy as np


def bytes_to_bits(data: bytes) -> np.ndarray:
    """Convert a bytes buffer into a 1D NumPy uint8 array of individual bits (MSB first).

    Args:
        data: Input bytes data.

    Returns:
        np.ndarray: 1D uint8 array of length len(data) * 8, containing 0s and 1s.
    """
    if len(data) == 0:
        return np.empty(0, dtype=np.uint8)

    byte_array = np.frombuffer(data, dtype=np.uint8)
    return np.unpackbits(byte_array)


def bits_to_bytes(bits: np.ndarray) -> bytes:
    """Pack a 1D NumPy array of bits into bytes (MSB first).

    Args:
        bits: 1D uint8 array of bits (length must be a multiple of 8).

    Returns:
        bytes: Packed binary bytes.

    Raises:
        ValueError: If the number of bits is not a multiple of 8.
    """
    if len(bits) == 0:
        return b""

    if len(bits) % 8 != 0:
        raise ValueError(
            f"Bit array length ({len(bits)}) must be a multiple of 8 to form complete bytes."
        )

    return np.packbits(bits).tobytes()


def embed_lsb(carrier_channels: np.ndarray, bits: np.ndarray) -> np.ndarray:
    """Embed bits into the least significant bit (LSB) of carrier pixel channel values.

    Core LSB operation:
        new_value = (old_value & 0xFE) | bit

    Args:
        carrier_channels: 1D uint8 array of carrier pixel channel values (R, G, B, ...).
        bits: 1D uint8 array of bits (0 or 1) to embed.

    Returns:
        np.ndarray: Modified 1D uint8 carrier channels array.

    Raises:
        ValueError: If bits array exceeds carrier channels length.
    """
    num_bits = len(bits)
    if num_bits > len(carrier_channels):
        raise ValueError(
            f"Insufficient carrier capacity: need {num_bits} channel slots, but carrier has only {len(carrier_channels)}."
        )

    modified = carrier_channels.copy()
    if num_bits > 0:
        modified[:num_bits] = (modified[:num_bits] & 0xFE) | bits

    return modified


def extract_lsb(
    carrier_channels: np.ndarray, num_bits: int, offset_bits: int = 0
) -> np.ndarray:
    """Extract a slice of LSB bits from carrier channel values.

    Extraction operation:
        bit = value & 0x01

    Args:
        carrier_channels: 1D uint8 array of carrier pixel channel values.
        num_bits: Number of bits to extract.
        offset_bits: Starting bit index in carrier_channels.

    Returns:
        np.ndarray: 1D uint8 array of extracted bits (0 or 1).

    Raises:
        ValueError: If requested range exceeds carrier channel length.
    """
    if num_bits < 0 or offset_bits < 0:
        raise ValueError("num_bits and offset_bits must be non-negative.")

    end_idx = offset_bits + num_bits
    if end_idx > len(carrier_channels):
        raise ValueError(
            f"Extraction range [{offset_bits}:{end_idx}] exceeds available carrier channels ({len(carrier_channels)})."
        )

    if num_bits == 0:
        return np.empty(0, dtype=np.uint8)

    return carrier_channels[offset_bits:end_idx] & 0x01


def extract_bytes(
    carrier_channels: np.ndarray, num_bytes: int, offset_bytes: int = 0
) -> bytes:
    """Extract a specified number of full bytes from carrier channels starting at an offset.

    Args:
        carrier_channels: 1D uint8 array of carrier pixel channel values.
        num_bytes: Number of bytes to extract.
        offset_bytes: Starting byte index in carrier.

    Returns:
        bytes: Extracted binary bytes.
    """
    if num_bytes == 0:
        return b""

    num_bits = num_bytes * 8
    offset_bits = offset_bytes * 8
    bits = extract_lsb(carrier_channels, num_bits, offset_bits)
    return bits_to_bytes(bits)
