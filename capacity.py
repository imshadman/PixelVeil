"""capacity.py - Steganographic capacity calculation module for RGB PNG images.

Calculates theoretical raw capacity and practical available payload headroom
based on image dimensions and binary header overhead.
"""

from typing import Dict, Tuple
from validators import StegoError

try:
    from metadata import get_header_size
except ImportError:
    get_header_size = None


class CapacityExceededError(StegoError):
    """Raised when the payload plus metadata exceeds the image capacity."""
    pass


def calculate_raw_capacity(width: int, height: int) -> Dict[str, int]:
    """Calculate the total raw steganographic capacity of an RGB image.

    Each pixel contains 3 color channels (R, G, B), providing 3 bits per pixel (1 LSB per channel).

    Formula:
        capacity_bits = width * height * 3
        capacity_bytes = capacity_bits // 8

    Args:
        width: Image width in pixels.
        height: Image height in pixels.

    Returns:
        Dict[str, int]: Capacity metrics (width, height, total_pixels, capacity_bits, capacity_bytes).
    """
    if width <= 0 or height <= 0:
        raise ValueError(f"Image dimensions must be positive integers: {width}x{height}")

    total_pixels = width * height
    capacity_bits = total_pixels * 3
    capacity_bytes = capacity_bits // 8

    return {
        "width": width,
        "height": height,
        "total_pixels": total_pixels,
        "capacity_bits": capacity_bits,
        "capacity_bytes": capacity_bytes,
    }


def get_actual_header_size(filename: str = "") -> int | None:
    """Get the actual serialized binary header size from metadata.py if implemented.

    Returns:
        int | None: Exact header size in bytes, or None if metadata.py is not yet implemented.
    """
    if get_header_size is not None:
        return get_header_size(filename)
    return None


def calculate_available_payload(width: int, height: int, filename: str = "") -> int | None:
    """Calculate the net usable payload capacity after accounting for actual metadata.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.
        filename: Target payload filename.

    Returns:
        int | None: Usable payload capacity in bytes, or None if header is not yet finalized.
    """
    raw = calculate_raw_capacity(width, height)
    header_size = get_actual_header_size(filename)
    if header_size is None:
        return None
    return max(0, raw["capacity_bytes"] - header_size)


def check_capacity(
    width: int, height: int, payload_size: int, filename: str = ""
) -> Tuple[bool, int, int]:
    """Check whether a payload and its metadata can fit inside an RGB image.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.
        payload_size: Size of the payload file in bytes (>= 0).
        filename: Payload filename.

    Returns:
        Tuple[bool, int, int]: (fits, total_required_bytes, total_capacity_bytes)
    """
    if payload_size < 0:
        raise ValueError(f"Payload size cannot be negative: {payload_size}")

    raw = calculate_raw_capacity(width, height)
    total_capacity = raw["capacity_bytes"]
    header_size = get_actual_header_size(filename)
    header_bytes = header_size if header_size is not None else 0
    total_required = header_bytes + payload_size

    fits = total_required <= total_capacity
    return fits, total_required, total_capacity


def validate_capacity(width: int, height: int, payload_size: int, filename: str = "") -> None:
    """Verify that the payload fits, raising CapacityExceededError if it does not.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.
        payload_size: Size of payload in bytes.
        filename: Filename for header estimation.

    Raises:
        CapacityExceededError: If required bytes exceed image capacity.
    """
    fits, total_required, total_capacity = check_capacity(width, height, payload_size, filename)
    if not fits:
        header_size = get_actual_header_size(filename)
        header_desc = f"{header_size} bytes" if header_size is not None else "pending metadata implementation"
        raise CapacityExceededError(
            f"Payload does not fit in image ({width}x{height}). "
            f"Payload size: {payload_size:,} bytes, Header: {header_desc}. "
            f"Total required: {total_required:,} bytes. "
            f"Maximum available capacity: {total_capacity:,} bytes. "
            f"Shortfall: {total_required - total_capacity:,} bytes."
        )


