"""crypto.py - Authenticated encryption module using AES-256-GCM and PBKDF2-HMAC-SHA256.

Phase 2 Extension:
Provides cryptographic key derivation, authenticated encryption, and authenticated
decryption.

Security Specification:
- Key Derivation Function: PBKDF2-HMAC-SHA256
    * Salt: 16 cryptographically secure random bytes (os.urandom(16))
    * Iterations: 100,000 (NIST / OWASP baseline)
    * Derived Key Length: 32 bytes (256 bits)
- Cipher: AES-256-GCM (Galois/Counter Mode)
    * Nonce: 12 cryptographically secure random bytes (os.urandom(12))
    * Authentication Tag: 16 bytes appended to ciphertext
    * Additional Authenticated Data (AAD): The complete serialized Version-2 header.
      Header authentication applies when AES-GCM encryption is enabled because
      the complete Version-2 header is passed as AES-GCM AAD.
"""

import os
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from validators import StegoError

PBKDF2_ITERATIONS = 100_000
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
TAG_SIZE = 16


class CryptoError(StegoError):
    """Base exception for encryption and decryption errors."""
    pass


class DecryptionError(CryptoError):
    """Raised when decryption or authentication tag verification fails."""
    pass


def derive_key(password: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> bytes:
    """Derive a 256-bit (32-byte) AES key from a user password using PBKDF2-HMAC-SHA256.

    Args:
        password: User-provided passphrase or key string.
        salt: 16-byte random cryptographic salt.
        iterations: Number of PBKDF2 iterations (default: 100,000).

    Returns:
        bytes: 32-byte derived AES-256 key.

    Raises:
        ValueError: If password is empty or salt is not 16 bytes.
    """
    if not password:
        raise ValueError("Password cannot be empty for encryption/decryption.")
    if len(salt) != SALT_SIZE:
        raise ValueError(f"Salt must be exactly {SALT_SIZE} bytes, got {len(salt)} bytes.")

    password_bytes = password.encode("utf-8")
    return hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=password_bytes,
        salt=salt,
        iterations=iterations,
        dklen=KEY_SIZE,
    )


def generate_salt() -> bytes:
    """Generate a 16-byte cryptographically secure random salt."""
    return os.urandom(SALT_SIZE)


def generate_nonce() -> bytes:
    """Generate a 12-byte cryptographically secure random nonce for AES-GCM."""
    return os.urandom(NONCE_SIZE)


def encrypt_payload(
    plaintext: bytes,
    key: bytes,
    nonce: bytes,
    associated_data: bytes = b"",
) -> bytes:
    """Encrypt plaintext using AES-256-GCM with Additional Authenticated Data (AAD).

    The resulting ciphertext contains the 16-byte authentication tag appended by AESGCM.

    Args:
        plaintext: Binary payload to encrypt.
        key: 32-byte AES key.
        nonce: 12-byte unique nonce.
        associated_data: Bytes to bind and authenticate via AAD (the complete serialized header).

    Returns:
        bytes: Ciphertext with 16-byte authentication tag appended.

    Raises:
        CryptoError: If encryption fails.
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"AES key must be exactly {KEY_SIZE} bytes, got {len(key)}")
    if len(nonce) != NONCE_SIZE:
        raise ValueError(f"AES-GCM nonce must be exactly {NONCE_SIZE} bytes, got {len(nonce)}")

    try:
        aesgcm = AESGCM(key)
        ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, associated_data)
        return ciphertext_with_tag
    except Exception as exc:
        raise CryptoError(f"AES-GCM encryption failed: {exc}") from exc


def decrypt_payload(
    ciphertext: bytes,
    key: bytes,
    nonce: bytes,
    associated_data: bytes = b"",
) -> bytes:
    """Decrypt ciphertext and verify the authentication tag using AES-256-GCM.

    Header authentication applies when AES-GCM encryption is enabled because
    the complete Version-2 header is used as AES-GCM AAD. If the password/key
    is incorrect or if either the ciphertext or the header metadata has been altered,
    decryption will fail.

    Args:
        ciphertext: Ciphertext with appended 16-byte authentication tag.
        key: 32-byte AES key.
        nonce: 12-byte nonce used during encryption.
        associated_data: Bytes to verify via AAD (the complete extracted header).

    Returns:
        bytes: Decrypted plaintext.

    Raises:
        DecryptionError: If the tag fails verification, password is wrong, or data is tampered.
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"AES key must be exactly {KEY_SIZE} bytes, got {len(key)}")
    if len(nonce) != NONCE_SIZE:
        raise ValueError(f"AES-GCM nonce must be exactly {NONCE_SIZE} bytes, got {len(nonce)}")

    try:
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data)
        return plaintext
    except InvalidTag as exc:
        raise DecryptionError(
            "AES-GCM authentication failed: invalid password or tampered data/header."
        ) from exc
    except Exception as exc:
        raise DecryptionError(f"Decryption failed: {exc}") from exc
