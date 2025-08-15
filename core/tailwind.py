# core/tailwind_remote.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
import re
import requests
import json5
import numpy as np
from .color_ops import hex_to_rgb, rgb_to_lab

# ---- Fallback: your compact, local subset (used if network fails) ----
FALLBACK_TAILWIND: Dict[str, Dict[int, str]] = {
    "slate": {200:"#e2e8f0",400:"#94a3b8",600:"#475569"},
    "gray": {200:"#e5e7eb",400:"#9ca3af",600:"#4b5563"},
    "zinc": {200:"#e4e4e7",400:"#a1a1aa",600:"#52525b"},
    "neutral": {200:"#e5e5e5",400:"#a3a3a3",600:"#525252"},
    "stone": {200:"#e7e5e4",400:"#a8a29e",600:"#57534e"},
    "red": {200:"#fecaca",400:"#f87171",600:"#dc2626"},
    "orange": {200:"#fed7aa",400:"#fb923c",600:"#ea580c"},
    "amber": {200:"#fde68a",400:"#f59e0b",600:"#d97706"},
    "yellow": {200:"#fef08a",400:"#facc15",600:"#ca8a04"},
    "lime": {200:"#d9f99d",400:"#84cc16",600:"#65a30d"},
    "green": {200:"#bbf7d0",400:"#22c55e",600:"#16a34a"},
    "emerald": {200:"#a7f3d0",400:"#10b981",600:"#059669"},
    "teal": {200:"#99f6e4",400:"#14b8a6",600:"#0d9488"},
    "cyan": {200:"#a5f3fc",400:"#22d3ee",600:"#0891b2"},
    "sky": {200:"#bae6fd",400:"#38bdf8",600:"#0284c7"},
    "blue": {200:"#bfdbfe",400:"#60a5fa",600:"#2563eb"},
    "indigo": {200:"#c7d2fe",400:"#818cf8",600:"#4f46e5"},
    "violet": {200:"#ddd6fe",400:"#a78bfa",600:"#7c3aed"},
    "purple": {200:"#e9d5ff",400:"#c084fc",600:"#9333ea"},
    "fuchsia": {200:"#fad6ff",400:"#e879f9",600:"#c026d3"},
    "pink": {200:"#fbcfe8",400:"#f472b6",600:"#db2777"},
    "rose": {200:"#fecdd3",400:"#fb7185",600:"#e11d48"},
}

CDN_CANDIDATES = [
    # Tailwind v3 line still exposes colors.js in the src/public folder
    # (exact version is configurable; 'latest_v3' is a convenience tag you can set)
    "https://cdn.jsdelivr.net/npm/tailwindcss@3.4.10/src/public/colors.js",
    "https://unpkg.com/tailwindcss@3.4.10/src/public/colors.js",
    # GitHub raw fallback (master branch may evolve)
    "https://raw.githubusercontent.com/tailwindlabs/tailwindcss/master/src/public/colors.js",
]

def _extract_js_object(js_text: str) -> str:
    """
    Extract the JS object from either `module.exports = {...}` or `export default {...}`.
    Returns the object literal as a string.
    """
    m = re.search(r"(module\\.exports\\s*=|export\\s+default)\\s*(\\{[\\s\\S]*\\})", js_text)
    if not m:
        raise ValueError("Could not locate object literal in colors.js")
    return m.group(2)

def fetch_tailwind_full_palette(timeout: float = 6.0) -> Dict[str, Dict[int, str]]:
    """
    Try several CDNs to fetch Tailwind's color palette.
    Returns a dict: { colorName: { shade:int -> hex:str } }.
    Filters out non-palette entries like 'black', 'white', 'transparent', 'current' if present.
    """
    last_err: Exception | None = None
    for url in CDN_CANDIDATES:
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            obj_text = _extract_js_object(r.text)
            raw = json5.loads(obj_text)  # tolerant parser (unquoted numeric keys, comments, etc.)
            # Keep only nested dicts with hex shades
            palette = {k: v for k, v in raw.items() if isinstance(v, dict)}
            # Ensure all shades are hex strings
            for name, shades in list(palette.items()):
                palette[name] = {int(s): str(hx) for s, hx in shades.items()}
            # optional: remove deprecated aliases if any (e.g., 'lightBlue' -> 'sky')
            palette.pop("lightBlue", None)
            palette.pop("warmGray", None)
            palette.pop("blueGray", None)
            return palette
        except Exception as e:
            last_err = e
            continue
    # Fallback to local subset if network fails
    if last_err:
        # You might want to log last_err to Streamlit console
        pass
    return FALLBACK_TAILWIND

@dataclass
class TWEntry:
    name: str
    shade: int
    hex: str

def build_tailwind_entries_and_lab_remote() -> Tuple[List[TWEntry], np.ndarray]:
    """
    Fetch Tailwind colors remotely (with fallback) and precompute LAB array.
    """
    palette = fetch_tailwind_full_palette()
    entries: List[TWEntry] = []
    rgbs: List[Tuple[int, int, int]] = []
    for name, shades in palette.items():
        for shade, hx in shades.items():
            entries.append(TWEntry(name=name, shade=shade, hex=hx))
            rgbs.append(hex_to_rgb(hx))
    rgb_arr = np.array(rgbs, dtype=np.uint8)
    lab_arr = rgb_to_lab(rgb_arr)
    return entries, lab_arr
