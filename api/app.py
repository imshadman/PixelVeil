"""app.py - Thin FastAPI adapter over existing steganography modules.

Rules strictly adhered to:
1. Thin wrapper only: No duplication of LSB logic, encryption, compression, metadata, or metrics.
2. Direct invocation of existing modules: validators, capacity, metadata, encoder, decoder, metrics.
3. Safe temporary file handling: No arbitrary local filesystem traversal or permanent storage.
4. Clean JSON schemas and streaming file downloads.
"""

import sys
import shutil
import tempfile
import json
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from validators import validate_cover_image, StegoError, UnsupportedImageError, FileValidationError
from capacity import calculate_raw_capacity, calculate_available_payload, check_capacity, CapacityExceededError
from metadata import (
    get_header_size,
    unpack_header_prefix,
    unpack_header,
    PREFIX_SIZE,
    FLAG_COMPRESSED,
    FLAG_ENCRYPTED,
    CorruptedHeaderError,
    InvalidMagicError,
    InvalidVersionError,
)
from bit_utils import extract_bytes
from encoder import encode_file
from decoder import decode_file, PasswordRequiredError
from crypto import DecryptionError
from metrics import evaluate_image_quality
from integrity import compute_file_sha256

app = FastAPI(
    title="File Steganography API",
    description="Thin FastAPI wrapper for RGB PNG LSB Steganography with Phase 1, 2, and 3 capabilities",
    version="2.0.0",
)

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated experiment plots statically if available
PLOTS_DIR = PROJECT_ROOT / "output" / "experiments" / "plots"
if PLOTS_DIR.exists():
    app.mount("/api/plots", StaticFiles(directory=str(PLOTS_DIR)), name="plots")


def remove_temp_dir(path: str):
    """Cleanup temporary directory callback."""
    try:
        shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


@app.get("/api/health")
def health_check():
    """System health check and module capability confirmation."""
    return {
        "status": "healthy",
        "phase1_core": True,
        "phase2_crypto_compression": True,
        "phase3_metrics": True,
    }


@app.post("/api/inspect-cover")
async def inspect_cover(cover: UploadFile = File(...)):
    """Inspect cover image and return dimensions, mode, and capacity."""
    if not cover.filename.lower().endswith(".png"):
        raise HTTPException(status_code=400, detail="Phase 1 supports RGB PNG images only.")

    with tempfile.TemporaryDirectory() as td:
        temp_cover = Path(td) / "cover.png"
        content = await cover.read()
        temp_cover.write_bytes(content)

        try:
            img = validate_cover_image(temp_cover)
            width, height = img.size
            raw = calculate_raw_capacity(width, height)
            baseline_header = get_header_size("sample.bin")
            max_payload = calculate_available_payload(width, height, "sample.bin")

            return {
                "filename": cover.filename,
                "format": img.format,
                "mode": img.mode,
                "width": width,
                "height": height,
                "total_pixels": raw["total_pixels"],
                "raw_capacity_bits": raw["capacity_bits"],
                "raw_capacity_bytes": raw["capacity_bytes"],
                "baseline_header_size": baseline_header,
                "max_payload_bytes": max_payload,
            }
        except UnsupportedImageError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except StegoError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/check-headroom")
async def check_headroom(
    cover: UploadFile = File(...),
    payload: UploadFile = File(...),
):
    """Check whether a specific payload will fit inside the chosen cover image."""
    with tempfile.TemporaryDirectory() as td:
        temp_cover = Path(td) / "cover.png"
        temp_cover.write_bytes(await cover.read())

        p_bytes = await payload.read()
        p_size = len(p_bytes)

        try:
            img = validate_cover_image(temp_cover)
            width, height = img.size
            filename = payload.filename or "payload.bin"
            header_size = get_header_size(filename)
            fits, required, capacity = check_capacity(width, height, p_size, filename)

            utilization = (required / capacity) * 100.0 if capacity > 0 else 0.0

            return {
                "cover_filename": cover.filename,
                "payload_filename": filename,
                "width": width,
                "height": height,
                "payload_size_bytes": p_size,
                "header_size_bytes": header_size,
                "total_required_bytes": required,
                "capacity_bytes": capacity,
                "remaining_bytes": max(0, capacity - required) if fits else 0,
                "shortfall_bytes": (required - capacity) if not fits else 0,
                "utilization_pct": round(utilization, 2),
                "fits": fits,
            }
        except StegoError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/encode")
async def encode_endpoint(
    background_tasks: BackgroundTasks,
    cover: UploadFile = File(...),
    payload: UploadFile = File(...),
    compress: bool = Form(False),
    password: Optional[str] = Form(None),
):
    """Embed payload into cover image using existing encoder.encode_file."""
    td = tempfile.mkdtemp(prefix="stego_encode_")
    td_path = Path(td)
    background_tasks.add_task(remove_temp_dir, td)

    cover_path = td_path / "cover.png"
    cover_path.write_bytes(await cover.read())

    payload_filename = payload.filename or "payload.bin"
    payload_path = td_path / payload_filename
    payload_path.write_bytes(await payload.read())

    stego_out_path = td_path / "stego.png"

    pwd = password.strip() if password and password.strip() else None

    try:
        stats = encode_file(
            cover_path=cover_path,
            payload_path=payload_path,
            output_path=stego_out_path,
            compress=compress,
            password=pwd,
        )

        headers = {
            "X-Payload-Filename": stats["payload_filename"],
            "X-Original-Size": str(stats["original_payload_bytes"]),
            "X-Embedded-Size": str(stats["embedded_payload_bytes"]),
            "X-Header-Size": str(stats["header_size_bytes"]),
            "X-Total-Embedded": str(stats["total_embedded_bytes"]),
            "X-Remaining-Capacity": str(stats["remaining_capacity_bytes"]),
            "X-Original-SHA256": stats["payload_sha256"],
            "X-Encoding-Time-Sec": str(stats["encoding_time_sec"]),
            "X-Is-Compressed": str(stats["is_compressed"]),
            "X-Is-Encrypted": str(stats["is_encrypted"]),
            "Access-Control-Expose-Headers": "X-Payload-Filename, X-Original-Size, X-Embedded-Size, X-Header-Size, X-Total-Embedded, X-Remaining-Capacity, X-Original-SHA256, X-Encoding-Time-Sec, X-Is-Compressed, X-Is-Encrypted",
        }

        return FileResponse(
            path=str(stego_out_path),
            filename="stego.png",
            media_type="image/png",
            headers=headers,
        )
    except CapacityExceededError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except StegoError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Encoding failed: {exc}")


@app.post("/api/probe-stego")
async def probe_stego(stego: UploadFile = File(...)):
    """Probe an uploaded stego image's header prefix without extracting payload."""
    with tempfile.TemporaryDirectory() as td:
        stego_path = Path(td) / "stego.png"
        stego_path.write_bytes(await stego.read())

        try:
            img = validate_cover_image(stego_path)
            import numpy as np
            pixel_array = np.array(img, dtype=np.uint8)
            flat_channels = pixel_array.reshape(-1)

            if len(flat_channels) // 8 < PREFIX_SIZE:
                raise HTTPException(status_code=400, detail="Image is too small to contain stego metadata.")

            prefix_bytes = extract_bytes(flat_channels, PREFIX_SIZE, offset_bytes=0)
            version, flags, total_header_len, name_len = unpack_header_prefix(prefix_bytes)

            full_header_bytes = extract_bytes(flat_channels, total_header_len, offset_bytes=0)
            header = unpack_header(full_header_bytes)

            return {
                "valid_stego": True,
                "version": header.version,
                "flags": header.flags,
                "is_compressed": header.is_compressed,
                "is_encrypted": header.is_encrypted,
                "filename": header.filename,
                "embedded_payload_bytes": header.payload_length,
                "expected_sha256": header.sha256_digest.hex(),
            }
        except (InvalidMagicError, InvalidVersionError, CorruptedHeaderError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except StegoError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/decode")
async def decode_endpoint(
    background_tasks: BackgroundTasks,
    stego: UploadFile = File(...),
    password: Optional[str] = Form(None),
):
    """Extract and recover payload from stego PNG image using existing decoder.decode_file."""
    td = tempfile.mkdtemp(prefix="stego_decode_")
    td_path = Path(td)
    background_tasks.add_task(remove_temp_dir, td)

    stego_path = td_path / "stego.png"
    stego_path.write_bytes(await stego.read())

    rec_dir = td_path / "recovered"
    pwd = password.strip() if password and password.strip() else None

    try:
        stats = decode_file(
            stego_path=stego_path,
            output_dir=rec_dir,
            password=pwd,
        )

        recovered_file = Path(stats["recovered_path"])
        if not recovered_file.exists():
            raise HTTPException(status_code=500, detail="Recovered file missing on disk.")

        headers = {
            "X-Recovered-Filename": stats["filename"],
            "X-Payload-Size": str(stats["payload_size_bytes"]),
            "X-Embedded-Size": str(stats["embedded_payload_bytes"]),
            "X-Protocol-Version": str(stats["version"]),
            "X-Is-Compressed": str(stats["is_compressed"]),
            "X-Is-Encrypted": str(stats["is_encrypted"]),
            "X-Original-SHA256": stats["expected_sha256"],
            "X-Recovered-SHA256": stats["actual_sha256"],
            "X-Integrity-Verified": str(stats["integrity_verified"]),
            "X-Decoding-Time-Sec": str(stats["decoding_time_sec"]),
            "Access-Control-Expose-Headers": "X-Recovered-Filename, X-Payload-Size, X-Embedded-Size, X-Protocol-Version, X-Is-Compressed, X-Is-Encrypted, X-Original-SHA256, X-Recovered-SHA256, X-Integrity-Verified, X-Decoding-Time-Sec",
        }

        return FileResponse(
            path=str(recovered_file),
            filename=stats["filename"],
            media_type="application/octet-stream",
            headers=headers,
        )
    except PasswordRequiredError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except DecryptionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except StegoError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Decoding failed: {exc}")


@app.post("/api/analyze")
async def analyze_endpoint(
    cover: UploadFile = File(...),
    stego: UploadFile = File(...),
):
    """Compare cover and stego images using existing metrics.evaluate_image_quality."""
    with tempfile.TemporaryDirectory() as td:
        p_cover = Path(td) / "cover.png"
        p_stego = Path(td) / "stego.png"

        p_cover.write_bytes(await cover.read())
        p_stego.write_bytes(await stego.read())

        try:
            img_c = validate_cover_image(p_cover)
            img_s = validate_cover_image(p_stego)

            quality = evaluate_image_quality(p_cover, p_stego)

            return {
                "cover_filename": cover.filename,
                "stego_filename": stego.filename,
                "width": img_c.width,
                "height": img_c.height,
                "mse": quality["mse"],
                "psnr_db": quality["psnr_db"] if quality["psnr_db"] != float("inf") else 999.0,
                "is_infinite_psnr": quality["psnr_db"] == float("inf"),
                "ssim": quality["ssim"],
                "visual_fidelity": "EXCELLENT" if quality["psnr_db"] > 50 else ("GOOD" if quality["psnr_db"] > 40 else "NOTICEABLE"),
            }
        except StegoError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/experiments")
def get_experiments():
    """Serve existing Phase 3 experimental benchmark results."""
    json_path = PROJECT_ROOT / "output" / "experiments" / "experiment_results.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Experiment results not found. Run run_experiments.py first.")

    with open(json_path, "r") as f:
        data = json.load(f)

    return {
        "results": data,
        "plots": [
            {"id": "psnr", "title": "PSNR vs. Payload Utilization", "url": "/api/plots/psnr_vs_utilization.png"},
            {"id": "mse", "title": "MSE vs. Payload Size", "url": "/api/plots/mse_vs_payload_size.png"},
            {"id": "ssim", "title": "SSIM vs. Payload Size", "url": "/api/plots/ssim_vs_payload_size.png"},
            {"id": "time", "title": "Execution Time Comparison", "url": "/api/plots/execution_time_comparison.png"},
        ],
    }
