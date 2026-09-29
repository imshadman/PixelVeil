"""run_experiments.py - Automated experimental benchmarking and quality analysis.

Phase 3: Image Quality and Performance Analysis.

Executes controlled steganography experiments:
- Resolutions: 2 cover image sizes (e.g. 250x250, 500x500)
- Payloads: 3 sizes (Small: ~500 B, Medium: ~3 KB, Large: ~15 KB)
- Payload Types: Text (.txt), Document (.pdf), and Binary (.bin)
- Modes: Plaintext, Compressed, and Encrypted

Measures and records for every run:
- Cover dimensions (width x height)
- Payload filename and type
- Payload size (bytes)
- Stego capacity (bytes)
- Payload utilization %
- Mean Squared Error (MSE)
- Peak Signal-to-Noise Ratio (PSNR in dB)
- Structural Similarity Index (SSIM)
- Encoding time (ms)
- Decoding time (ms)
- SHA-256 integrity match confirmation
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image
import numpy as np

from encoder import encode_file
from decoder import decode_file
from metrics import evaluate_image_quality
from integrity import compute_file_sha256


def generate_experiment_assets(base_dir: Path) -> Dict[str, Any]:
    """Create controlled test images and payload files for experiments."""
    assets_dir = base_dir / "experiment_assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # 1. Resolutions: Small (250x250) and Large (500x500)
    # 250x250 RGB capacity = 250 * 250 * 3 // 8 = 23,437 bytes
    # 500x500 RGB capacity = 500 * 500 * 3 // 8 = 93,750 bytes
    img_250 = assets_dir / "cover_250x250.png"
    img_500 = assets_dir / "cover_500x500.png"

    # Create synthetic gradient images with varied textures for realistic IVP analysis
    arr_250 = np.zeros((250, 250, 3), dtype=np.uint8)
    for y in range(250):
        for x in range(250):
            arr_250[y, x] = [int((x / 250) * 200) + 20, int((y / 250) * 180) + 30, int(((x + y) / 500) * 190) + 40]
    Image.fromarray(arr_250).save(img_250, format="PNG")

    arr_500 = np.zeros((500, 500, 3), dtype=np.uint8)
    for y in range(500):
        for x in range(500):
            arr_500[y, x] = [int((x / 500) * 220) + 15, int((y / 500) * 210) + 20, int(((x * y) / 250000) * 200) + 30]
    Image.fromarray(arr_500).save(img_500, format="PNG")

    # 2. Payloads:
    # Size 1 (Small): ~500 B (PDF document)
    pdf_path = assets_dir / "payload_small_500B.pdf"
    pdf_bytes = (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Length 120 >>\nstream\n"
        b"BT /F1 12 Tf 72 700 Td (Experiment Small PDF Payload for IVP Steganography) Tj ET\n"
        b"endstream\nendobj\nxref\n0 5\n0000000000 65535 f \n"
        b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n340\n%%EOF\n"
    )
    # Pad to exactly ~500 B
    pdf_bytes += b"%" + b"A" * (500 - len(pdf_bytes) - 1) + b"\n"
    pdf_path.write_bytes(pdf_bytes)

    # Size 2 (Medium): ~3,000 B (Text report)
    txt_path = assets_dir / "payload_medium_3KB.txt"
    txt_content = ("IVP Steganography Benchmarking Report - Performance & Image Quality Analysis.\n" * 38)[:3000]
    txt_path.write_text(txt_content)

    # Size 3 (Large): ~15,000 B (Raw binary data)
    bin_path = assets_dir / "payload_large_15KB.bin"
    np.random.seed(42)
    bin_path.write_bytes(bytes(np.random.randint(0, 256, 15000, dtype=np.uint8)))

    return {
        "covers": [
            {"path": img_250, "res": "250x250", "capacity": 23437},
            {"path": img_500, "res": "500x500", "capacity": 93750},
        ],
        "payloads": [
            {"path": pdf_path, "type": "PDF", "name": "Small (~500 B)", "size": len(pdf_bytes)},
            {"path": txt_path, "type": "TXT", "name": "Medium (~3 KB)", "size": len(txt_content.encode('utf-8'))},
            {"path": bin_path, "type": "BIN", "name": "Large (~15 KB)", "size": 15000},
        ],
    }


def run_all_experiments() -> List[Dict[str, Any]]:
    """Execute matrix of experiments across resolutions, payload sizes, and security modes."""
    base_dir = Path("output") / "experiments"
    base_dir.mkdir(parents=True, exist_ok=True)

    assets = generate_experiment_assets(base_dir)
    results: List[Dict[str, Any]] = []

    exp_id = 1
    # Run combinations
    for cover in assets["covers"]:
        for payload in assets["payloads"]:
            cover_path = cover["path"]
            payload_path = payload["path"]

            # Modes:
            # Mode A: Plaintext (Phase 1)
            # Mode B: Compressed + Encrypted (Phase 2)
            modes = [
                {"name": "Plain LSB", "compress": False, "password": None},
                {"name": "zlib + AES-GCM", "compress": True, "password": "ExpSecurePassword123!"},
            ]

            for mode in modes:
                stego_name = f"stego_exp{exp_id}_{cover['res']}_{payload['type']}.png"
                stego_path = base_dir / stego_name
                rec_dir = base_dir / f"rec_exp{exp_id}"

                # 1. Encode
                enc_stats = encode_file(
                    cover_path=cover_path,
                    payload_path=payload_path,
                    output_path=stego_path,
                    compress=mode["compress"],
                    password=mode["password"],
                )

                # 2. Decode
                dec_stats = decode_file(
                    stego_path=stego_path,
                    output_dir=rec_dir,
                    password=mode["password"],
                )

                # 3. Verify exact recovery
                orig_bytes = payload_path.read_bytes()
                rec_file = rec_dir / payload_path.name
                rec_bytes = rec_file.read_bytes()
                assert orig_bytes == rec_bytes, f"Recovery mismatch for Exp {exp_id}"

                _, orig_sha = compute_file_sha256(payload_path)
                _, rec_sha = compute_file_sha256(rec_file)
                assert orig_sha == rec_sha, f"SHA-256 mismatch for Exp {exp_id}"

                # 4. Measure Image Quality
                quality = evaluate_image_quality(cover_path, stego_path)

                capacity_bytes = cover["capacity"]
                embedded_bytes = enc_stats["total_embedded_bytes"]
                utilization_pct = (embedded_bytes / capacity_bytes) * 100.0

                record = {
                    "exp_id": exp_id,
                    "resolution": cover["res"],
                    "payload_name": payload["name"],
                    "payload_type": payload["type"],
                    "payload_size_bytes": payload["size"],
                    "mode": mode["name"],
                    "embedded_stream_bytes": enc_stats["embedded_payload_bytes"],
                    "total_embedded_bytes": embedded_bytes,
                    "capacity_bytes": capacity_bytes,
                    "utilization_pct": round(utilization_pct, 2),
                    "mse": round(quality["mse"], 6),
                    "psnr_db": round(quality["psnr_db"], 2),
                    "ssim": round(quality["ssim"], 6),
                    "encode_time_ms": round(enc_stats["encoding_time_sec"] * 1000, 2),
                    "decode_time_ms": round(dec_stats["decoding_time_sec"] * 1000, 2),
                    "integrity_verified": True,
                }
                results.append(record)
                exp_id += 1

    # Save results JSON
    json_path = base_dir / "experiment_results.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    records = run_all_experiments()
    print(f"Successfully executed {len(records)} experiments.")
