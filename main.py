"""main.py - Command-Line Interface for File Steganography in RGB PNG Images.

Phase 1 & Phase 2 LSB Steganography CLI.
Provides commands for capacity inspection, payload headroom checking,
and steganographic encoding / decoding with optional zlib compression
and AES-256-GCM authenticated encryption.
"""

import sys
import argparse
from pathlib import Path
from validators import (
    validate_cover_image,
    validate_payload_file,
    StegoError,
    UnsupportedImageError,
    FileValidationError,
)
from capacity import (
    calculate_raw_capacity,
    calculate_available_payload,
    get_actual_header_size,
    check_capacity,
    CapacityExceededError,
)
from encoder import encode_file
from decoder import decode_file


def format_bytes(size: int) -> str:
    """Format byte size in human-readable notation (B, KB, MB)."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB ({size:,} bytes)"
    else:
        return f"{size / (1024 * 1024):.2f} MB ({size:,} bytes)"


def cmd_info(args: argparse.Namespace) -> int:
    """Display image dimensions and steganographic capacity."""
    image_path = Path(args.image)
    try:
        img = validate_cover_image(image_path)
    except StegoError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    width, height = img.size
    metrics = calculate_raw_capacity(width, height)
    actual_header_size = get_actual_header_size()
    max_payload = calculate_available_payload(width, height)

    print("=" * 60)
    print("IMAGE STEGANOGRAPHY - CAPACITY INFO")
    print("=" * 60)
    print(f"Image File:        {image_path.name}")
    print(f"Image Format:      {img.format}")
    print(f"Color Mode:        {img.mode} (3 channels: R, G, B)")
    print(f"Dimensions:        {width} x {height} px")
    print(f"Total Pixels:      {metrics['total_pixels']:,} px")
    print("-" * 60)
    print(f"Raw Capacity:      {metrics['capacity_bits']:,} bits")
    print(f"                   {format_bytes(metrics['capacity_bytes'])}")
    if actual_header_size is None or max_payload is None:
        print("Header Size:       Not finalized yet")
        print("Maximum Payload:   Will be calculated after metadata/header implementation")
    else:
        print(f"Header Size:       {actual_header_size} bytes (V2 baseline)")
        print(f"Maximum Payload:   {format_bytes(max_payload)}")
    print("=" * 60)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Check if a specific payload file will fit inside the cover image."""
    image_path = Path(args.image)
    payload_path = Path(args.payload)

    try:
        img = validate_cover_image(image_path)
        p_path, p_size = validate_payload_file(payload_path)
    except StegoError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    width, height = img.size
    filename = p_path.name
    actual_header_size = get_actual_header_size(filename)
    fits, required, capacity = check_capacity(width, height, p_size, filename)

    print("=" * 60)
    print("CAPACITY & HEADROOM ANALYSIS")
    print("=" * 60)
    print(f"Cover Image:       {image_path.name} ({width} x {height} px)")
    print(f"Payload File:      {filename}")
    print(f"Payload Size:      {format_bytes(p_size)}")
    if actual_header_size is None:
        print("Header Overhead:   Not finalized yet")
        print(f"Total Required:    At least {format_bytes(required)} (payload only; header pending)")
    else:
        print(f"Header Overhead:   {actual_header_size} bytes (V2)")
        print(f"Total Required:    {format_bytes(required)}")
    print(f"Stego Capacity:    {format_bytes(capacity)}")
    print("-" * 60)

    if fits:
        headroom = capacity - required
        utilization = (required / capacity) * 100 if capacity > 0 else 0
        status_note = " (excluding header)" if actual_header_size is None else ""
        print(f"Status:            FITS [PASS]{status_note}")
        print(f"Remaining Room:    {format_bytes(headroom)}")
        print(f"Utilization:       {utilization:.2f}% of capacity used")
        print("=" * 60)
        return 0
    else:
        shortfall = required - capacity
        print(f"Status:            DOES NOT FIT [FAIL]")
        print(f"Shortfall:         Needs {format_bytes(shortfall)} more capacity")
        print("=" * 60)
        return 1


def cmd_encode(args: argparse.Namespace) -> int:
    """Encode an arbitrary payload file into an RGB PNG cover image with optional compression/encryption."""
    cover_path = Path(args.cover)
    payload_path = Path(args.payload)
    output_path = Path(args.output) if args.output else Path("output") / "stego.png"

    try:
        stats = encode_file(
            cover_path=cover_path,
            payload_path=payload_path,
            output_path=output_path,
            compress=args.compress,
            password=args.password,
        )
    except StegoError as e:
        print(f"Encoding Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected Error during encoding: {e}", file=sys.stderr)
        return 1

    feature_desc = []
    if stats["is_compressed"]:
        feature_desc.append("zlib Compression")
    if stats["is_encrypted"]:
        feature_desc.append("AES-256-GCM Encryption")
    mode_str = " + ".join(feature_desc) if feature_desc else "None (Plain LSB)"

    print("=" * 60)
    print("IMAGE STEGANOGRAPHY - ENCODING SUMMARY")
    print("=" * 60)
    print(f"Cover Image:          {cover_path.name}")
    print(f"Cover Dimensions:     {stats['width']} x {stats['height']} px ({stats['total_pixels']:,} px)")
    print(f"Raw Capacity:         {format_bytes(stats['raw_capacity_bytes'])}")
    print(f"Payload File:         {stats['payload_filename']}")
    print(f"Original Size:        {format_bytes(stats['original_payload_bytes'])}")
    print(f"Embedded Size:        {format_bytes(stats['embedded_payload_bytes'])}")
    print(f"Header Size:          {stats['header_size_bytes']} bytes (V2)")
    print(f"Total Embedded:       {format_bytes(stats['total_embedded_bytes'])}")
    print(f"Remaining Capacity:   {format_bytes(stats['remaining_capacity_bytes'])}")
    print(f"Security / Processing: {mode_str}")
    print(f"Stego Output:         {stats['output_path']}")
    print(f"Original SHA-256:     {stats['payload_sha256']}")
    print(f"Encoding Time:        {stats['encoding_time_sec'] * 1000:.2f} ms ({stats['encoding_time_sec']:.4f} s)")
    print("-" * 60)
    print("Status:               ENCODING SUCCESSFUL [PASS]")
    print("=" * 60)
    return 0


def cmd_decode(args: argparse.Namespace) -> int:
    """Extract a hidden file from an RGB PNG stego image."""
    stego_path = Path(args.stego)
    output_dir = Path(args.output_dir) if args.output_dir else Path("output")

    try:
        stats = decode_file(
            stego_path=stego_path,
            output_dir=output_dir,
            password=args.password,
        )
    except StegoError as e:
        print(f"Decoding Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected Error during decoding: {e}", file=sys.stderr)
        return 1

    feature_desc = []
    if stats["is_compressed"]:
        feature_desc.append("zlib Decompressed")
    if stats["is_encrypted"]:
        feature_desc.append("AES-256-GCM Decrypted")
    mode_str = " + ".join(feature_desc) if feature_desc else "None (Plain LSB)"

    print("=" * 60)
    print("IMAGE STEGANOGRAPHY - DECODING SUMMARY")
    print("=" * 60)
    print(f"Stego Image:          {stego_path.name}")
    print(f"Protocol Version:     Version {stats['version']}")
    print(f"Dimensions:           {stats['width']} x {stats['height']} px")
    print(f"Recovered File:       {stats['filename']}")
    print(f"Saved Path:           {stats['recovered_path']}")
    print(f"Original Size:        {format_bytes(stats['payload_size_bytes'])}")
    print(f"Extracted Stream:     {format_bytes(stats['embedded_payload_bytes'])}")
    print(f"Header Size:          {stats['header_size_bytes']} bytes")
    print(f"Processing:           {mode_str}")
    print(f"Expected SHA-256:     {stats['expected_sha256']}")
    print(f"Recovered SHA-256:    {stats['actual_sha256']}")
    print(f"Decoding Time:        {stats['decoding_time_sec'] * 1000:.2f} ms ({stats['decoding_time_sec']:.4f} s)")
    print("-" * 60)
    print("Integrity verification: PASS")
    print("SHA-256:                MATCH")
    print("Status:                 DECODING SUCCESSFUL [PASS]")
    print("=" * 60)
    return 0


from metrics import evaluate_image_quality


def cmd_analyze(args: argparse.Namespace) -> int:
    """Compare cover and stego images, computing MSE, PSNR, and SSIM."""
    cover_path = Path(args.cover)
    stego_path = Path(args.stego)

    try:
        results = evaluate_image_quality(cover_path, stego_path)
    except StegoError as e:
        print(f"Analysis Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected Error during quality analysis: {e}", file=sys.stderr)
        return 1

    print("=" * 60)
    print("IMAGE QUALITY ANALYSIS (PHASE 3)")
    print("=" * 60)
    print(f"Cover Image:          {cover_path.name}")
    print(f"Stego Image:          {stego_path.name}")
    print("-" * 60)
    print(f"Mean Squared Error (MSE):       {results['mse']:.6f}")
    if results["psnr_db"] == float("inf"):
        print(f"Peak Signal-to-Noise (PSNR):    Infinity (Identical Images)")
    else:
        print(f"Peak Signal-to-Noise (PSNR):    {results['psnr_db']:.2f} dB")
    print(f"Structural Similarity (SSIM):   {results['ssim']:.6f}")
    print("-" * 60)
    if results["psnr_db"] > 50.0:
        print("Visual Fidelity:                EXCELLENT (Imperceptible modification)")
    elif results["psnr_db"] > 40.0:
        print("Visual Fidelity:                GOOD (Near-imperceptible modification)")
    else:
        print("Visual Fidelity:                NOTICEABLE")
    print("=" * 60)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="image_steganography",
        description="File Steganography in RGB PNG Images Using LSB Encoding (Phase 1, 2 & 3)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # info command
    info_parser = subparsers.add_parser("info", help="Inspect image capacity")
    info_parser.add_argument("image", help="Path to the RGB PNG cover image")
    info_parser.set_defaults(func=cmd_info)

    # check command
    check_parser = subparsers.add_parser("check", help="Check if payload fits in image")
    check_parser.add_argument("image", help="Path to the RGB PNG cover image")
    check_parser.add_argument("payload", help="Path to the payload file to test")
    check_parser.set_defaults(func=cmd_check)

    # encode command
    encode_parser = subparsers.add_parser("encode", help="Embed payload into cover image")
    encode_parser.add_argument("cover", help="Path to the RGB PNG cover image")
    encode_parser.add_argument("payload", help="Path to payload file to hide")
    encode_parser.add_argument(
        "-o", "--output", help="Path for stego PNG image (default: output/stego.png)"
    )
    encode_parser.add_argument(
        "-c", "--compress", action="store_true", help="Compress payload with zlib before embedding"
    )
    encode_parser.add_argument(
        "-p", "--password", help="Encrypt payload with AES-256-GCM using this passphrase"
    )
    encode_parser.set_defaults(func=cmd_encode)

    # decode command
    decode_parser = subparsers.add_parser("decode", help="Extract hidden file from stego image")
    decode_parser.add_argument("stego", help="Path to stego PNG image")
    decode_parser.add_argument(
        "-o", "--output-dir", help="Directory to save recovered file (default: output/)"
    )
    decode_parser.add_argument(
        "-p", "--password", help="Password for AES-256-GCM decryption if payload is encrypted"
    )
    decode_parser.set_defaults(func=cmd_decode)

    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Compare cover and stego images (MSE, PSNR, SSIM)")
    analyze_parser.add_argument("cover", help="Path to original RGB PNG cover image")
    analyze_parser.add_argument("stego", help="Path to stego RGB PNG image")
    analyze_parser.set_defaults(func=cmd_analyze)

    return parser


def main() -> int:
    """Main application entry point."""
    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        return 1

    args = parser.parse_args()
    if hasattr(args, "func"):
        return args.func(args)
    else:
        parser.print_help(sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
