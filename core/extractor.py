from typing import Tuple
import numpy as np
from PIL import Image
import cv2

def kmeans_colors(
    image: Image.Image,
    k: int = 6,
    sample: int = 400_000,
    seed: int = 42,
    max_side: int = 1024
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Return (centers:uint8[K,3], weights:float[K]) for dominant colors using k-means.
    - Downscales large images for speed.
    - Uses full (downscaled) frame to estimate cluster weights.
    """
    img = image.convert("RGB")
    arr = np.array(img)
    h, w, _ = arr.shape

    # Optional downscale
    if max(h, w) > max_side:
        scale = max_side / max(h, w)
        arr = cv2.resize(arr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    pixels = arr.reshape(-1, 3).astype(np.float32)

    # Subsample for k-means speed if needed
    if pixels.shape[0] > sample:
        rng = np.random.default_rng(seed)
        idx = rng.choice(pixels.shape[0], size=sample, replace=False)
        data = pixels[idx]
    else:
        data = pixels

    # OpenCV kmeans
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.2)
    _, _, centers = cv2.kmeans(data, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    centers = centers.clip(0, 255).astype(np.uint8)

    # Estimate weights by assigning all pixels (downscaled) to nearest center
    centers_f = centers.astype(np.float32)
    diffs = arr.reshape(-1, 1, 3).astype(np.float32) - centers_f[None, :, :]
    d2 = (diffs ** 2).sum(axis=2)  # (N,K)
    labels = d2.argmin(axis=1)     # (N,)
    counts = np.bincount(labels, minlength=k)
    weights = counts / counts.sum()

    # Sort by prevalence
    order = (-weights).argsort()
    return centers[order], weights[order]
