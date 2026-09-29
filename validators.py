"""validators.py - Input and image format validation module for LSB steganography.

Enforces Phase 1 constraints:
- Only RGB mode PNG images are supported.
- Payload files must exist and be accessible.
- Filename sanitization against directory traversal.
- Safety check to prevent overwriting cover images.
"""

from pathlib import Path
from typing import Tuple
from PIL import Image, UnidentifiedImageError


class StegoError(Exception):
    """Base exception for all steganography errors."""
    pass


class UnsupportedImageError(StegoError):
    """Raised when an image format or mode is not supported."""
    pass


class FileValidationError(StegoError):
    """Raised when an input or output file is invalid or inaccessible."""
    pass


def validate_cover_image(image_path: Path | str) -> Image.Image:
    """Validate that the given image is an existing, non-corrupted RGB PNG image.

    Args:
        image_path: Path to the image file.

    Returns:
        PIL.Image.Image: The opened RGB PNG image instance.

    Raises:
        FileValidationError: If file does not exist or is not a file.
        UnsupportedImageError: If the format is not PNG or mode is not RGB.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileValidationError(f"Cover image file does not exist: {path}")
    if not path.is_file():
        raise FileValidationError(f"Specified cover image path is not a file: {path}")

    try:
        image = Image.open(path)
        # Ensure image data can be decoded
        image.load()
    except UnidentifiedImageError as exc:
        raise UnsupportedImageError(
            f"Cannot identify image file '{path.name}'. Phase 1 supports RGB PNG images only."
        ) from exc
    except Exception as exc:
        raise FileValidationError(f"Failed to open image '{path.name}': {exc}") from exc

    # Enforce strict PNG format
    if image.format != "PNG":
        fmt = image.format or "Unknown"
        raise UnsupportedImageError(
            f"Image format '{fmt}' is unsupported. Phase 1 supports RGB PNG images only."
        )

    # Enforce strict RGB mode (reject RGBA, L, P, CMYK, etc.)
    if image.mode != "RGB":
        raise UnsupportedImageError(
            f"Image color mode '{image.mode}' is unsupported. Phase 1 supports RGB PNG images only."
        )

    return image


def validate_payload_file(payload_path: Path | str) -> Tuple[Path, int]:
    """Validate that the payload file exists and determine its size in bytes.

    Supports arbitrary binary files, including 0-byte (empty) files.

    Args:
        payload_path: Path to the payload file.

    Returns:
        Tuple[Path, int]: The resolved Path object and its file size in bytes.

    Raises:
        FileValidationError: If file does not exist, is a directory, or cannot be read.
    """
    path = Path(payload_path)
    if not path.exists():
        raise FileValidationError(f"Payload file does not exist: {path}")
    if not path.is_file():
        raise FileValidationError(f"Payload path is not a regular file: {path}")

    try:
        # Verify read access in binary mode
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
        return path, size
    except PermissionError as exc:
        raise FileValidationError(f"Permission denied reading payload: {path}") from exc
    except Exception as exc:
        raise FileValidationError(f"Failed to access payload file '{path}': {exc}") from exc


def sanitize_filename(filename: str) -> str:
    """Strip directory path components and prevent directory traversal attacks.

    Args:
        filename: Untrusted filename extracted from metadata or user input.

    Returns:
        str: Sanitized, basename-only filename.
    """
    if not filename:
        return "recovered_file.bin"

    # Extract base name to remove any path elements (e.g., ../../secret.txt -> secret.txt)
    safe_name = Path(filename).name

    # Remove null bytes or any leading/trailing whitespace
    safe_name = safe_name.replace("\x00", "").strip()

    if not safe_name or safe_name in (".", ".."):
        return "recovered_file.bin"

    return safe_name


def validate_output_path(cover_path: Path | str, output_path: Path | str) -> Path:
    """Ensure the output stego image path does not overwrite the original cover image.

    Args:
        cover_path: Path to the original cover image.
        output_path: Proposed destination path for the stego image.

    Returns:
        Path: Resolved output path.

    Raises:
        FileValidationError: If output path points to the same file as cover image.
    """
    cov = Path(cover_path).resolve()
    out = Path(output_path).resolve()

    if cov == out:
        raise FileValidationError(
            f"Output path '{out}' cannot be the same as the cover image. "
            "Never overwrite the original cover image."
        )

    # Ensure parent directory exists
    out.parent.mkdir(parents=True, exist_ok=True)
    return out
