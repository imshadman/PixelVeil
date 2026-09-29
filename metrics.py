"""metrics.py - Image quality and steganographic performance evaluation module.

Provides mathematical implementations for:
1. Mean Squared Error (MSE)
2. Peak Signal-to-Noise Ratio (PSNR)
3. Structural Similarity Index Measure (SSIM)
4. Comprehensive quality comparison between cover and stego images.
"""

import math
from pathlib import Path
from typing import Dict, Tuple, Union
import numpy as np
from PIL import Image

from validators import validate_cover_image, StegoError


class MetricComputationError(StegoError):
    """Raised when metric calculation fails due to incompatible image shapes or formats."""
    pass


def calculate_mse(image_a: np.ndarray, image_b: np.ndarray) -> float:
    """Calculate the Mean Squared Error (MSE) between two images.

    Formula:
        MSE = (1 / (M * N * C)) * sum((I_A(x, y, c) - I_B(x, y, c))^2)

    Args:
        image_a: Original RGB image array (H, W, 3) or (H, W) in uint8 or float.
        image_b: Stego RGB image array of identical dimensions.

    Returns:
        float: Mean squared error value (0.0 means identical images).

    Raises:
        MetricComputationError: If image dimensions or shapes mismatch.
    """
    if image_a.shape != image_b.shape:
        raise MetricComputationError(
            f"Image shapes must match: {image_a.shape} vs {image_b.shape}"
        )

    # Convert to float64 to prevent overflow during subtraction and squaring
    diff = image_a.astype(np.float64) - image_b.astype(np.float64)
    mse = np.mean(diff ** 2)
    return float(mse)


def calculate_psnr(image_a: np.ndarray, image_b: np.ndarray, max_val: float = 255.0) -> float:
    """Calculate the Peak Signal-to-Noise Ratio (PSNR) in decibels (dB).

    Formula:
        PSNR = 10 * log10(MAX_I^2 / MSE)

    If MSE == 0 (identical images), PSNR is theoretically infinite. We return float('inf').

    Args:
        image_a: Original RGB image array.
        image_b: Stego RGB image array.
        max_val: Maximum possible pixel intensity (255.0 for 8-bit channels).

    Returns:
        float: PSNR in decibels (dB), or float('inf') if MSE is 0.
    """
    mse = calculate_mse(image_a, image_b)
    if mse == 0.0:
        return float("inf")

    psnr = 10.0 * math.log10((max_val ** 2) / mse)
    return float(psnr)


def calculate_ssim(
    image_a: np.ndarray,
    image_b: np.ndarray,
    k1: float = 0.01,
    k2: float = 0.03,
    l_val: float = 255.0,
    window_size: int = 11,
) -> float:
    """Calculate the Structural Similarity Index Measure (SSIM) between two images.

    Implementation follows the Wang et al. (2004) structural similarity model:
        SSIM(x, y) = [ (2*mu_x*mu_y + c1)*(2*sigma_xy + c2) ] /
                     [ (mu_x^2 + mu_y^2 + c1)*(sigma_x^2 + sigma_y^2 + c2) ]

    A circular/separable Gaussian window of size window_size with sigma=1.5 is applied.
    For multichannel RGB images, SSIM is computed per channel and averaged.

    Args:
        image_a: Original RGB image array (H, W, 3) or 2D (H, W).
        image_b: Stego RGB image array.
        k1: Algorithm parameter (default 0.01).
        k2: Algorithm parameter (default 0.03).
        l_val: Dynamic range of pixel values (255 for 8-bit).
        window_size: Gaussian window filter size (must be odd, default 11).

    Returns:
        float: SSIM index ranging from -1.0 to 1.0 (1.0 means identical).
    """
    if image_a.shape != image_b.shape:
        raise MetricComputationError(
            f"Image shapes must match: {image_a.shape} vs {image_b.shape}"
        )

    # 1D Gaussian kernel
    sigma = 1.5
    half_size = window_size // 2
    x = np.arange(-half_size, half_size + 1, dtype=np.float64)
    kernel_1d = np.exp(-(x ** 2) / (2.0 * sigma ** 2))
    kernel_1d /= np.sum(kernel_1d)

    def _filter2d(img: np.ndarray) -> np.ndarray:
        """Separable 2D convolution with reflect padding."""
        # Horizontal pass
        padded_h = np.pad(img, ((0, 0), (half_size, half_size)), mode="reflect")
        # Vectorized 1D convolution over horizontal
        temp = np.zeros_like(img, dtype=np.float64)
        for i in range(window_size):
            temp += kernel_1d[i] * padded_h[:, i : i + img.shape[1]]

        # Vertical pass
        padded_v = np.pad(temp, ((half_size, half_size), (0, 0)), mode="reflect")
        out = np.zeros_like(img, dtype=np.float64)
        for i in range(window_size):
            out += kernel_1d[i] * padded_v[i : i + img.shape[0], :]
        return out

    c1 = (k1 * l_val) ** 2
    c2 = (k2 * l_val) ** 2

    def _ssim_single_channel(ch_a: np.ndarray, ch_b: np.ndarray) -> float:
        a = ch_a.astype(np.float64)
        b = ch_b.astype(np.float64)

        mu_a = _filter2d(a)
        mu_b = _filter2d(b)

        mu_a_sq = mu_a ** 2
        mu_b_sq = mu_b ** 2
        mu_ab = mu_a * mu_b

        sigma_a_sq = _filter2d(a ** 2) - mu_a_sq
        sigma_b_sq = _filter2d(b ** 2) - mu_b_sq
        sigma_ab = _filter2d(a * b) - mu_ab

        numerator = (2.0 * mu_ab + c1) * (2.0 * sigma_ab + c2)
        denominator = (mu_a_sq + mu_b_sq + c1) * (sigma_a_sq + sigma_b_sq + c2)

        ssim_map = numerator / denominator
        return float(np.mean(ssim_map))

    if image_a.ndim == 2:
        return _ssim_single_channel(image_a, image_b)
    elif image_a.ndim == 3:
        num_channels = image_a.shape[2]
        channel_ssims = [
            _ssim_single_channel(image_a[:, :, c], image_b[:, :, c])
            for c in range(num_channels)
        ]
        return float(np.mean(channel_ssims))
    else:
        raise MetricComputationError(f"Unsupported array dimensionality: {image_a.ndim}")


def evaluate_image_quality(
    cover_path: Union[Path, str],
    stego_path: Union[Path, str],
) -> Dict[str, float]:
    """Load cover and stego images and compute complete quality metrics.

    Args:
        cover_path: Path to original cover RGB PNG image.
        stego_path: Path to stego RGB PNG image.

    Returns:
        Dict[str, float]: Dictionary containing:
            - 'mse': Mean Squared Error
            - 'psnr_db': Peak Signal-to-Noise Ratio in dB
            - 'ssim': Structural Similarity Index
    """
    img_cover = validate_cover_image(cover_path)
    img_stego = validate_cover_image(stego_path)

    if img_cover.size != img_stego.size:
        raise MetricComputationError(
            f"Image dimensions mismatch: Cover {img_cover.size} vs Stego {img_stego.size}"
        )

    arr_cover = np.array(img_cover, dtype=np.uint8)
    arr_stego = np.array(img_stego, dtype=np.uint8)

    mse = calculate_mse(arr_cover, arr_stego)
    psnr = calculate_psnr(arr_cover, arr_stego)
    ssim = calculate_ssim(arr_cover, arr_stego)

    return {
        "mse": mse,
        "psnr_db": psnr,
        "ssim": ssim,
    }
