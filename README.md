# File Steganography in RGB PNG Images Using LSB Encoding

**Course**: Image and Video Processing (IVP) Mini-Project  
**Status**: Phase 1, Phase 2 & Phase 3 Complete (100% Implemented, Tested, and Benchmarked)

---

## 1. Project Objective

The primary objective of this project is to implement a robust, modular, and mathematically sound steganographic system capable of embedding arbitrary binary files (such as `.txt`, `.pdf`, `.jpg`, `.zip`, etc.) into RGB PNG images using spatial domain Least Significant Bit (LSB) substitution. The system guarantees lossless payload recovery using PNG-based LSB steganography with SHA-256 cryptographic verification, enhanced in Phase 2 with optional zlib compression and AES-256-GCM authenticated encryption, and evaluated in Phase 3 with rigorous image quality (MSE, PSNR, SSIM) and performance analysis.

---

## 2. How LSB Steganography Works

In an 8-bit color channel, pixel intensity values range from $0$ to $255$ ($00000000_2$ to $11111111_2$). 
The least significant bit (LSB, bit 0) carries the smallest weight ($2^0 = 1$), contributing minimally to human visual perception:

$$\Delta I \le 1 \implies \frac{\Delta I}{255} \approx 0.39\%$$

### LSB Replacement Logic
To embed a binary bit $b \in \{0, 1\}$ into an existing channel intensity $v_{\text{old}}$:

$$v_{\text{new}} = (v_{\text{old}} \ \& \ \text{0xFE}) \ | \ b$$

- Bitwise AND with `0xFE` ($11111110_2$) clears the LSB to $0$.
- Bitwise OR with $b$ sets the LSB to the target payload bit.

### LSB Extraction Logic
During decoding, the hidden bit is recovered by masking out all higher-order bits:

$$b = v_{\text{stego}} \ \& \ \text{0x01}$$

Eight consecutive extracted bits are packed to reconstruct one original byte.

---

## 3. Why RGB PNG is Used

1. **Lossless Compression**: PNG uses the DEFLATE algorithm (LZ77 + Huffman coding), ensuring exact reconstruction of pixel data without altering a single bit. Lossy compression formats (such as JPEG) apply discrete cosine transforms (DCT) and quantization that destroy spatial LSBs.
2. **Fixed Channel Depth**: Standard RGB images provide 3 channels (Red, Green, Blue) per pixel, yielding a deterministic capacity of 3 bits per pixel.
3. **Strict Constraints**: Non-RGB formats (Grayscale `L`, Alpha-channel `RGBA`, Palette `P`) are strictly rejected to prevent ambiguity and unintended channel distortion.

---

## 4. Steganographic Capacity Formula

For an RGB image of resolution $W \times H$:

$$\text{Capacity}_{\text{bits}} = W \times H \times 3$$

$$\text{Capacity}_{\text{bytes}} = \left\lfloor \frac{\text{Capacity}_{\text{bits}}}{8} \right\rfloor$$

$$\text{Available Payload}_{\text{bytes}} = \text{Capacity}_{\text{bytes}} - \text{Header Size}_{\text{bytes}}$$

*Note: Steganographic capacity depends strictly on pixel dimensions, never on PNG disk file size.*

---

## 5. Binary Header Specifications

The system supports deterministic Big-Endian binary headers:

### Version 2 (Current Phase 2 & 3 Default):
Total size: $78 + N$ bytes (where $N = \text{len}(\text{filename})$).

| Offset (Bytes) | Field Name | Type / Struct | Size | Purpose |
|---|---|---|---|---|
| `0 .. 3` | `MAGIC` | `4s` | 4 B | Signature identifier: `b"STEG"` |
| `4` | `VERSION` | `B` | 1 B | Protocol version: `2` |
| `5` | `FLAGS` | `B` | 1 B | Feature flags: `0x00`=none, `0x01`=zlib, `0x02`=AES-GCM, `0x03`=both |
| `6 .. 7` | `HEADER_LENGTH` | `>H` | 2 B | Total header size ($78 + N$ bytes) |
| `8 .. 9` | `FILENAME_LENGTH` | `>H` | 2 B | Filename byte length ($N$) |
| `10 .. 10+N-1` | `FILENAME` | `Ns` | $N$ B | Sanitized UTF-8 payload filename |
| `10+N .. 17+N` | `PAYLOAD_LENGTH`| `>Q` | 8 B | Exact embedded stream size in bytes |
| `18+N .. 33+N` | `SALT` | `16s` | 16 B | 16-byte PBKDF2 salt (zeros if unencrypted) |
| `34+N .. 45+N` | `NONCE` | `12s` | 12 B | 12-byte AES-GCM nonce (zeros if unencrypted) |
| `46+N .. 77+N` | `ORIGINAL_SHA256`| `32s` | 32 B | SHA-256 digest of original plaintext |

### Version 1 (Legacy Phase 1 Backward Compatibility):
Total size: $50 + N$ bytes. Decoded seamlessly by the system without salt or nonce fields.

---

## 6. Compression & Authenticated Encryption (Phase 2)

### A. Lossless Compression (zlib)
Payloads can be optionally compressed prior to encryption and embedding using `zlib.compress(level=6)`, significantly reducing the carrier capacity needed for text, logs, or uncompressed formats.

### B. Authenticated Encryption (AES-256-GCM)
- **Key Derivation**: PBKDF2-HMAC-SHA256 with 100,000 iterations and a 16-byte cryptographically random salt (`os.urandom(16)`).
- **Cipher**: AES-256-GCM with a 12-byte unique random nonce (`os.urandom(12)`).
- **Header Authentication via AAD**: Header authentication applies when AES-GCM encryption is enabled because the complete Version-2 header is passed as AES-GCM Additional Authenticated Data (AAD). Any modification to header metadata causes authentication tag verification to fail during decryption.

---

## 7. Image Quality & Performance Analysis (Phase 3)

The [metrics.py](metrics.py) module provides rigorous spatial-domain image fidelity analysis:

1. **Mean Squared Error (MSE)**:
   $$\text{MSE} = \frac{1}{M \cdot N \cdot 3} \sum_{x=0}^{M-1} \sum_{y=0}^{N-1} \sum_{c=0}^{2} \left[ I_{\text{cover}}(x, y, c) - I_{\text{stego}}(x, y, c) \right]^2$$
2. **Peak Signal-to-Noise Ratio (PSNR)**:
   $$\text{PSNR} = 10 \cdot \log_{10}\left( \frac{255^2}{\text{MSE}} \right) \quad (\text{in dB})$$
   *Note: Values above $50\text{ dB}$ represent imperceptible differences to the human eye.*
3. **Structural Similarity Index (SSIM)**:
   Wang et al. Gaussian-weighted structural index capturing luminance, contrast, and structure:
   $$\text{SSIM}(x, y) = \frac{(2\mu_x\mu_y + C_1)(2\sigma_{xy} + C_2)}{(\mu_x^2 + \mu_y^2 + C_1)(\sigma_x^2 + \sigma_y^2 + C_2)}$$

### Experimental Benchmarks Summary (12 Controlled Experiments):
- **Cover Resolutions**: $250\times 250$ ($23,437$ B capacity) and $500\times 500$ ($93,750$ B capacity).
- **Payload Sizes Tested**: Small (~$500$ B), Medium (~$3$ KB), Large (~$15$ KB).
- **Quality Results**:
  - Across all experiments, **PSNR remained between $53.03\text{ dB}$ and $77.40\text{ dB}$**, far exceeding the standard human visual threshold ($50\text{ dB}$).
  - **SSIM remained above $0.9949$** (up to $0.99999$), confirming structural preservation.
  - Encoding time averaged **$12$–$50\text{ ms}$**, and decoding time averaged **$6$–$60\text{ ms}$**.

---

## 8. Installation & Requirements

```bash
py -m pip install pillow numpy cryptography matplotlib
```

---

## 9. How to Run

### Check Image Capacity
```bash
py main.py info input/cover.png
```

### Check Payload Fit & Headroom
```bash
py main.py check input/cover.png input/example.pdf
```

### Encode (with Compression + Encryption)
```bash
py main.py encode input/cover.png input/example.pdf -o output/stego.png -c -p "SecretKey2026!"
```

### Decode & Recover
```bash
py main.py decode output/stego.png -o output/recovered -p "SecretKey2026!"
```

### Quality Analysis (MSE, PSNR, SSIM)
```bash
py main.py analyze input/cover.png output/stego.png
```

### Run Full Benchmark Experiments & Generate Graphs
```bash
py run_experiments.py
py generate_plots.py
```

### Run All Unit & API Tests (47 Tests)
```bash
py -m pytest
```

---

## 10. Web Application & API (Modern React + FastAPI)

The project includes a web user interface with dark mode, real-time capacity headroom bars, drag-and-drop file upload, stego probe previews, MSE/PSNR/SSIM analysis, and interactive experiment visualizers.

### Architecture
- **Backend**: FastAPI (`api/app.py`) acting as a thin adapter over `encoder.py`, `decoder.py`, `capacity.py`, and `metrics.py`. Uses temporary directories for safe payload processing without permanent storage or filesystem exposure.
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide icons (`frontend/`).

### Running the Web Application
1. **Start FastAPI Backend**:
   ```bash
   py -m uvicorn api.app:app --host 127.0.0.1 --port 8000
   ```
2. **Start Frontend Dev Server**:
   ```bash
   cd frontend
   npm run dev -- --host 127.0.0.1 --port 5173
   ```
3. Open `http://127.0.0.1:5173` in your web browser.

