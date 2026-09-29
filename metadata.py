"""metadata.py - Deterministic binary header serialization for LSB steganography.

Binary Header Specifications:
=============================
All multi-byte numeric fields are encoded in Big-Endian (Network Byte Order: '>').

Version 1 (Phase 1 legacy):
+-------------------+-----------------+------------------------------------------+
| Offset (Bytes)    | Format / Size   | Field & Purpose                          |
+-------------------+-----------------+------------------------------------------+
| 0 .. 3            | 4s (4 bytes)    | MAGIC: b"STEG" signature identifier      |
| 4                 | B  (1 byte)     | VERSION: 1                               |
| 5                 | B  (1 byte)     | FLAGS: 0x00                              |
| 6 .. 7            | >H (2 bytes)    | HEADER_LENGTH: 50 + N                    |
| 8 .. 9            | >H (2 bytes)    | FILENAME_LENGTH: Filename byte count (N) |
| 10 .. (10+N-1)    | Ns (N bytes)    | FILENAME: UTF-8 sanitized filename bytes |
| (10+N) .. (17+N)  | >Q (8 bytes)    | PAYLOAD_LENGTH: Payload size in bytes    |
| (18+N) .. (49+N)  | 32s (32 bytes)  | ORIGINAL_SHA256: Raw 32-byte hash digest |
+-------------------+-----------------+------------------------------------------+
Total V1 Base Size = 50 + N bytes.

Version 2 (Phase 2 current):
+-------------------+-----------------+------------------------------------------+
| Offset (Bytes)    | Format / Size   | Field & Purpose                          |
+-------------------+-----------------+------------------------------------------+
| 0 .. 3            | 4s (4 bytes)    | MAGIC: b"STEG" signature identifier      |
| 4                 | B  (1 byte)     | VERSION: 2                               |
| 5                 | B  (1 byte)     | FLAGS: 0x00=plain, 0x01=comp, 0x02=enc,  |
|                   |                 |        0x03=comp+enc                     |
| 6 .. 7            | >H (2 bytes)    | HEADER_LENGTH: 78 + N                    |
| 8 .. 9            | >H (2 bytes)    | FILENAME_LENGTH: Filename byte count (N) |
| 10 .. (10+N-1)    | Ns (N bytes)    | FILENAME: UTF-8 sanitized filename bytes |
| (10+N) .. (17+N)  | >Q (8 bytes)    | PAYLOAD_LENGTH: Embedded payload size    |
| (18+N) .. (33+N)  | 16s (16 bytes)  | SALT: 16-byte PBKDF2 salt (or zeros)     |
| (34+N) .. (45+N)  | 12s (12 bytes)  | NONCE: 12-byte AES-GCM nonce (or zeros)  |
| (46+N) .. (77+N)  | 32s (32 bytes)  | ORIGINAL_SHA256: Raw 32-byte hash digest |
+-------------------+-----------------+------------------------------------------+
Total V2 Base Size = 78 + N bytes.
"""

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Optional
from validators import StegoError, sanitize_filename

MAGIC = b"STEG"
VERSION_1 = 1
VERSION_2 = 2
CURRENT_VERSION = VERSION_2

# Flag definitions
FLAG_NONE = 0x00
FLAG_COMPRESSED = 0x01
FLAG_ENCRYPTED = 0x02
FLAG_COMPRESSED_AND_ENCRYPTED = 0x03

# Fixed prefix: MAGIC(4s) + VERSION(B) + FLAGS(B) + HEADER_LENGTH(H) + FILENAME_LENGTH(H)
PREFIX_FORMAT = ">4sBBHH"
PREFIX_SIZE = struct.calcsize(PREFIX_FORMAT)  # 10 bytes

# Version 1 suffix: PAYLOAD_LENGTH(Q) + SHA256(32s)
SUFFIX_V1_FORMAT = ">Q32s"
SUFFIX_V1_SIZE = struct.calcsize(SUFFIX_V1_FORMAT)  # 40 bytes
BASE_HEADER_SIZE_V1 = PREFIX_SIZE + SUFFIX_V1_SIZE  # 50 bytes

# Version 2 suffix: PAYLOAD_LENGTH(Q) + SALT(16s) + NONCE(12s) + SHA256(32s)
SUFFIX_V2_FORMAT = ">Q16s12s32s"
SUFFIX_V2_SIZE = struct.calcsize(SUFFIX_V2_FORMAT)  # 68 bytes
BASE_HEADER_SIZE_V2 = PREFIX_SIZE + SUFFIX_V2_SIZE  # 78 bytes

# Current default base header size
BASE_HEADER_SIZE = BASE_HEADER_SIZE_V2


class HeaderError(StegoError):
    """Base exception for metadata and header parsing errors."""
    pass


class InvalidMagicError(HeaderError):
    """Raised when the extracted magic signature does not match b'STEG'."""
    pass


class InvalidVersionError(HeaderError):
    """Raised when the header version is unsupported."""
    pass


class CorruptedHeaderError(HeaderError):
    """Raised when header size or fields are invalid or corrupted."""
    pass


@dataclass(frozen=True)
class Header:
    """Parsed steganography header."""
    version: int
    flags: int
    header_length: int
    filename: str
    payload_length: int
    sha256_digest: bytes
    salt: bytes = b"\x00" * 16
    nonce: bytes = b"\x00" * 12

    @property
    def is_compressed(self) -> bool:
        return bool(self.flags & FLAG_COMPRESSED)

    @property
    def is_encrypted(self) -> bool:
        return bool(self.flags & FLAG_ENCRYPTED)


def get_header_size(filename: str = "", version: int = CURRENT_VERSION) -> int:
    """Calculate the exact serialized header size for a given filename in bytes.

    Args:
        filename: Payload filename (will be sanitized and UTF-8 encoded).
        version: Header protocol version (1 or 2). Default is 2.

    Returns:
        int: Actual byte length of the serialized header.
    """
    safe_name = sanitize_filename(filename) if filename else ""
    name_bytes = safe_name.encode("utf-8")
    base_size = BASE_HEADER_SIZE_V1 if version == 1 else BASE_HEADER_SIZE_V2
    return base_size + len(name_bytes)


def pack_header(
    filename: str,
    payload_length: int,
    sha256_digest: bytes,
    flags: int = FLAG_NONE,
    salt: Optional[bytes] = None,
    nonce: Optional[bytes] = None,
    version: int = CURRENT_VERSION,
) -> bytes:
    """Serialize the steganography header into deterministic binary bytes.

    For Version 2 (default):
    - Base header size: 78 bytes.
    - If unencrypted, salt and nonce default to zero-bytes.

    For Version 1:
    - Base header size: 50 bytes (legacy Phase 1 format).

    Args:
        filename: Original payload filename.
        payload_length: Size of embedded payload stream in bytes (>= 0).
        sha256_digest: 32 raw bytes of original uncompressed, plaintext payload SHA-256.
        flags: Feature flags (FLAG_NONE, FLAG_COMPRESSED, FLAG_ENCRYPTED, etc.).
        salt: 16-byte PBKDF2 salt (required for encrypted V2, or zeros).
        nonce: 12-byte AES-GCM nonce (required for encrypted V2, or zeros).
        version: Protocol version (1 or 2).

    Returns:
        bytes: The packed binary header.
    """
    if payload_length < 0:
        raise ValueError(f"Payload length cannot be negative: {payload_length}")

    if len(sha256_digest) != 32:
        raise ValueError(f"SHA-256 digest must be exactly 32 raw bytes, got {len(sha256_digest)}")

    safe_name = sanitize_filename(filename) if filename else ""
    name_bytes = safe_name.encode("utf-8")
    name_len = len(name_bytes)

    if name_len > 65535:
        raise ValueError(f"Filename is too long ({name_len} bytes; max 65535 bytes)")

    if version == VERSION_1:
        total_header_len = BASE_HEADER_SIZE_V1 + name_len
        prefix = struct.pack(PREFIX_FORMAT, MAGIC, VERSION_1, 0, total_header_len, name_len)
        suffix = struct.pack(SUFFIX_V1_FORMAT, payload_length, sha256_digest)
        serialized = prefix + name_bytes + suffix
    elif version == VERSION_2:
        total_header_len = BASE_HEADER_SIZE_V2 + name_len
        salt_bytes = salt if salt is not None else (b"\x00" * 16)
        nonce_bytes = nonce if nonce is not None else (b"\x00" * 12)

        if len(salt_bytes) != 16:
            raise ValueError(f"Salt must be exactly 16 bytes, got {len(salt_bytes)}")
        if len(nonce_bytes) != 12:
            raise ValueError(f"Nonce must be exactly 12 bytes, got {len(nonce_bytes)}")

        prefix = struct.pack(PREFIX_FORMAT, MAGIC, VERSION_2, flags, total_header_len, name_len)
        suffix = struct.pack(SUFFIX_V2_FORMAT, payload_length, salt_bytes, nonce_bytes, sha256_digest)
        serialized = prefix + name_bytes + suffix
    else:
        raise ValueError(f"Unsupported header version: {version}")

    assert len(serialized) == total_header_len, "Serialized size mismatch"
    return serialized


def unpack_header_prefix(prefix_bytes: bytes) -> Tuple[int, int, int, int]:
    """Unpack and validate the initial 10-byte header prefix.

    Args:
        prefix_bytes: First 10 bytes extracted from carrier image.

    Returns:
        Tuple[int, int, int, int]: (version, flags, total_header_len, name_len)

    Raises:
        CorruptedHeaderError: If prefix is less than 10 bytes.
        InvalidMagicError: If magic signature does not match b"STEG".
        InvalidVersionError: If version is neither 1 nor 2.
    """
    if len(prefix_bytes) < PREFIX_SIZE:
        raise CorruptedHeaderError(
            f"Truncated header prefix: expected {PREFIX_SIZE} bytes, got {len(prefix_bytes)}"
        )

    magic, version, flags, total_header_len, name_len = struct.unpack(
        PREFIX_FORMAT, prefix_bytes[:PREFIX_SIZE]
    )

    if magic != MAGIC:
        raise InvalidMagicError(
            f"Invalid stego magic signature '{magic!r}'. Cover image does not contain valid stego data."
        )

    if version not in (VERSION_1, VERSION_2):
        raise InvalidVersionError(
            f"Unsupported stego version {version}. Supported versions are {VERSION_1} and {VERSION_2}."
        )

    expected_base = BASE_HEADER_SIZE_V1 if version == VERSION_1 else BASE_HEADER_SIZE_V2
    expected_len = expected_base + name_len
    if total_header_len != expected_len:
        raise CorruptedHeaderError(
            f"Corrupted header length: header specifies {total_header_len} bytes, "
            f"expected {expected_len} bytes for version {version} and filename length {name_len}."
        )

    return version, flags, total_header_len, name_len


def unpack_header(header_bytes: bytes) -> Header:
    """Unpack complete binary header bytes into a Header dataclass instance.

    Supports both Version 1 and Version 2 headers.

    Args:
        header_bytes: Full serialized header bytes.

    Returns:
        Header: Validated Header instance.

    Raises:
        CorruptedHeaderError: If data is corrupted, truncated, or invalid.
    """
    version, flags, total_header_len, name_len = unpack_header_prefix(header_bytes)

    if len(header_bytes) < total_header_len:
        raise CorruptedHeaderError(
            f"Truncated header: expected {total_header_len} bytes, got {len(header_bytes)}"
        )

    name_start = PREFIX_SIZE
    name_end = name_start + name_len
    name_bytes = header_bytes[name_start:name_end]

    try:
        filename = name_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CorruptedHeaderError("Corrupted filename in header: invalid UTF-8") from exc

    filename = sanitize_filename(filename)
    suffix_bytes = header_bytes[name_end:total_header_len]

    if version == VERSION_1:
        if len(suffix_bytes) < SUFFIX_V1_SIZE:
            raise CorruptedHeaderError(
                f"Truncated V1 header suffix: expected {SUFFIX_V1_SIZE} bytes, got {len(suffix_bytes)}"
            )
        payload_length, sha256_digest = struct.unpack(SUFFIX_V1_FORMAT, suffix_bytes[:SUFFIX_V1_SIZE])
        return Header(
            version=version,
            flags=0,
            header_length=total_header_len,
            filename=filename,
            payload_length=payload_length,
            sha256_digest=sha256_digest,
            salt=b"\x00" * 16,
            nonce=b"\x00" * 12,
        )
    else:  # VERSION_2
        if len(suffix_bytes) < SUFFIX_V2_SIZE:
            raise CorruptedHeaderError(
                f"Truncated V2 header suffix: expected {SUFFIX_V2_SIZE} bytes, got {len(suffix_bytes)}"
            )
        payload_length, salt, nonce, sha256_digest = struct.unpack(
            SUFFIX_V2_FORMAT, suffix_bytes[:SUFFIX_V2_SIZE]
        )
        return Header(
            version=version,
            flags=flags,
            header_length=total_header_len,
            filename=filename,
            payload_length=payload_length,
            sha256_digest=sha256_digest,
            salt=salt,
            nonce=nonce,
        )
