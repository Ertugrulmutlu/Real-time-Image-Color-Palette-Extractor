from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
import cv2

# ----- Low-level color helpers -----
def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)

def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """
    Convert uint8 RGB array shape (N,3) -> LAB float32 (N,3) using OpenCV.
    """
    bgr = rgb[:, ::-1].astype(np.uint8)           # OpenCV expects BGR
    bgr = bgr[np.newaxis, :, :]                   # (1,N,3)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)[0] # (N,3)
    return lab.astype(np.float32)

# ----- ΔE 1976 -----
def deltaE76(lab1: np.ndarray, lab2: np.ndarray) -> np.ndarray:
    """
    Compute ΔE*ab 1976 distances between lab1 (N,3) and lab2 (M,3).
    Returns (N,M) distances.
    """
    a = lab1[:, None, :]
    b = lab2[None, :, :]
    d = np.sqrt(np.sum((a - b) ** 2, axis=2))
    return d

# ----- ΔE 2000 (CIEDE2000) -----
def deltaE2000(lab1: np.ndarray, lab2: np.ndarray) -> np.ndarray:
    """
    Vectorized CIEDE2000 implementation.
    lab1: (N,3) float32/64  [L*, a*, b*]
    lab2: (M,3) float32/64
    Returns: (N,M) distances
    """
    L1, a1, b1 = lab1[:, 0:1], lab1[:, 1:2], lab1[:, 2:3]   # (N,1)
    L2, a2, b2 = lab2[None, :, 0], lab2[None, :, 1], lab2[None, :, 2]  # (1,M)

    # Mean C*
    C1 = np.sqrt(a1**2 + b1**2)        # (N,1)
    C2 = np.sqrt(a2**2 + b2**2)        # (1,M)
    C_bar = (C1 + C2) / 2.0

    # G factor
    C_bar7 = C_bar**7
    G = 0.5 * (1 - np.sqrt(C_bar7 / (C_bar7 + (25.0**7))))

    # a' (prime)
    a1p = (1 + G) * a1
    a2p = (1 + G) * a2
    C1p = np.sqrt(a1p**2 + b1**2)
    C2p = np.sqrt(a2p**2 + b2**2)

    # h' (prime) in radians
    def _atan2(y, x):
        ang = np.arctan2(y, x)
        ang = np.where(ang < 0, ang + 2*np.pi, ang)
        return ang

    h1p = _atan2(b1, a1p)  # (N,1)
    h2p = _atan2(b2, a2p)  # (1,M)

    # ΔL', ΔC', Δh'
    dLp = L1 - L2
    dCp = C1p - C2p

    dhp = h2p - h1p
    dhp = np.where(dhp >  np.pi, dhp - 2*np.pi, dhp)
    dhp = np.where(dhp < -np.pi, dhp + 2*np.pi, dhp)
    dHp = 2.0 * np.sqrt(C1p * C2p) * np.sin(dhp / 2.0)

    # L', C', h' means
    Lp_bar = (L1 + L2) / 2.0
    Cp_bar = (C1p + C2p) / 2.0

    hp_bar = (h1p + h2p) / 2.0
    hp_bar = np.where(np.abs(h1p - h2p) > np.pi, hp_bar + np.pi, hp_bar)
    hp_bar = np.where(hp_bar >= 2*np.pi, hp_bar - 2*np.pi, hp_bar)

    # T term
    T = (1
         - 0.17*np.cos(hp_bar - np.deg2rad(30))
         + 0.24*np.cos(2*hp_bar)
         + 0.32*np.cos(3*hp_bar + np.deg2rad(6))
         - 0.20*np.cos(4*hp_bar - np.deg2rad(63)))

    # SL, SC, SH
    SL = 1 + (0.015 * (Lp_bar - 50)**2) / np.sqrt(20 + (Lp_bar - 50)**2)
    SC = 1 + 0.045 * Cp_bar
    SH = 1 + 0.015 * Cp_bar * T

    # Δθ, RC, RT
    delta_theta = np.deg2rad(30) * np.exp(- ((np.rad2deg(hp_bar) - 275) / 25)**2)
    RC = 2 * np.sqrt(Cp_bar**7 / (Cp_bar**7 + 25.0**7))
    RT = -np.sin(2 * delta_theta) * RC

    # kL=kC=kH=1
    kL = kC = kH = 1.0

    # Final ΔE00
    dE = np.sqrt(
        (dLp / (kL * SL))**2 +
        (dCp / (kC * SC))**2 +
        (dHp / (kH * SH))**2 +
        RT * (dCp / (kC * SC)) * (dHp / (kH * SH))
    )

    return dE.astype(np.float32)

# ----- Matching to Tailwind -----
@dataclass
class TWMatch:
    name: str
    shade: int
    hex: str
    deltaE: float

def nearest_tailwind(
    rgb: Tuple[int, int, int],
    tw_entries: List,
    tw_lab: np.ndarray,
    method: str = "DE76"
) -> TWMatch:
    """
    Return nearest Tailwind color for a single RGB color.
    method: "DE76" or "DE2000"
    """
    rgb_lab = rgb_to_lab(np.array([rgb], dtype=np.uint8))  # (1,3)
    if method.upper() in ("DE2000", "CIEDE2000", "DE00"):
        dists = deltaE2000(rgb_lab, tw_lab)[0]
    else:
        dists = deltaE76(rgb_lab, tw_lab)[0]

    k = int(np.argmin(dists))
    entry = tw_entries[k]
    return TWMatch(name=entry.name, shade=entry.shade, hex=entry.hex, deltaE=float(dists[k]))

# --- Accessibility helpers ---
def _srgb_to_lin(c: float) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 * 255 else ((c + 0.055 * 255) / (1.055 * 255)) ** 2.4

def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    r, g, b = rgb
    R = _srgb_to_lin(r)
    G = _srgb_to_lin(g)
    B = _srgb_to_lin(b)
    return 0.2126 * R + 0.7152 * G + 0.0722 * B

def contrast_ratio(rgb1: Tuple[int,int,int], rgb2: Tuple[int,int,int]) -> float:
    L1 = relative_luminance(rgb1)
    L2 = relative_luminance(rgb2)
    L1, L2 = (L1, L2) if L1 >= L2 else (L2, L1)
    return (L1 + 0.05) / (L2 + 0.05)

def ideal_text_color(bg: Tuple[int,int,int]) -> Tuple[int,int,int]:
    """Return black or white depending on which has higher contrast on bg."""
    black = (0,0,0)
    white = (255,255,255)
    return white if contrast_ratio(bg, white) >= contrast_ratio(bg, black) else black
