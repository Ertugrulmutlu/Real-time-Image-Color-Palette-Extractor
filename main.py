import io
import json
import colorsys

import streamlit as st
from PIL import Image

from core.tailwind import build_tailwind_entries_and_lab_remote
from core.color_ops import (
    rgb_to_hex,
    TWMatch,
    nearest_tailwind,
    ideal_text_color,
    contrast_ratio,
)
from core.extractor import kmeans_colors
from core.ui import render_palette_grid

st.set_page_config(page_title="Real-time Palette Extractor", page_icon="🎨", layout="wide")

@st.cache_resource
def _load_tailwind_cache():
    return build_tailwind_entries_and_lab_remote()

TW_ENTRIES, TW_LAB = _load_tailwind_cache()

st.markdown("""
# 🎨 Real-time Image Color Palette Extractor
- Extract dominant colors using **k-means**
- Map each centroid to the nearest **Tailwind** color in **LAB**
- Generate **CSS variables**, `tailwind.config.js` snippet, and **JSON** export

> Upload an image on the left, see the palette on the right.
""")

with st.sidebar:
    st.header("Settings")
    k = st.slider("Number of colors (k-means)", 3, 12, 6)
    show_tailwind = st.checkbox("Show Tailwind matches", value=True)
    show_percentages = st.checkbox("Show percentages", value=True)
    use_de2000 = st.checkbox("Use ΔE2000 (more accurate)", value=True)

    sort_by = st.selectbox(
        "Sort palette by",
        ["weight (desc)", "hue (asc)", "luminance (asc)"],
        index=0,
    )

    st.markdown("---")
    st.caption("💡 Tip: PNG/JPEG recommended. Large images are auto-downscaled.")

col_img, col_pal = st.columns([1, 1.2])

with col_img:
    file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"])
    if file:
        image = Image.open(io.BytesIO(file.read()))
        st.image(image, use_column_width=True, caption="Uploaded image")
    else:
        st.info("Upload an image to get started.")

with col_pal:
    if not file:
        st.empty()
    else:
        centers, weights = kmeans_colors(image, k=k)

        items = []
        css_vars = []
        tw_tokens = []

        def rgb_to_hsv_deg(rgb):
            r, g, b = [v / 255.0 for v in rgb]
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            return h * 360.0, s, v

        def luminance(rgb):
            r, g, b = rgb
            return 0.2126 * (r/255.0) + 0.7152 * (g/255.0) + 0.0722 * (b/255.0)

        method = "DE2000" if use_de2000 else "DE76"
        delta_label = "ΔE2000" if use_de2000 else "ΔE76"

        raw_items = []
        for idx, (c, w) in enumerate(zip(centers, weights), start=1):
            rgb = tuple(int(x) for x in c.tolist())
            hexv = rgb_to_hex(rgb)

            tw = None
            if show_tailwind:
                twm = nearest_tailwind(rgb, TW_ENTRIES, TW_LAB, method=method)
                tw = {"token": f"{twm.name}-{twm.shade}", "hex": twm.hex, "deltaE": twm.deltaE, "delta_label": delta_label}

            itc = ideal_text_color(rgb)
            cr_b = contrast_ratio(rgb, (0, 0, 0))
            cr_w = contrast_ratio(rgb, (255, 255, 255))
            best_cr = max(cr_b, cr_w)
            if best_cr >= 7:
                wcag = "AAA"
            elif best_cr >= 4.5:
                wcag = "AA"
            elif best_cr >= 3:
                wcag = "AA (Large)"
            else:
                wcag = "N/A"

            raw_items.append({
                "index": idx,
                "hex": hexv,
                "rgb": rgb,
                "weight": float(w),
                "tailwind": tw,
                "ideal_text": f"rgb({itc[0]},{itc[1]},{itc[2]})",
                "cr_black": cr_b,
                "cr_white": cr_w,
                "wcag_label": wcag,
                "_hue": rgb_to_hsv_deg(rgb)[0],
                "_lum": luminance(rgb),
            })

        if sort_by == "weight (desc)":
            items = sorted(raw_items, key=lambda x: -x["weight"])
        elif sort_by == "hue (asc)":
            items = sorted(raw_items, key=lambda x: x["_hue"])
        else:
            items = sorted(raw_items, key=lambda x: x["_lum"])

        for i, it in enumerate(items, start=1):
            css_vars.append(f"--color-{i}: {it['hex']};")
            if it["tailwind"]:
                tw_tokens.append(f'"color-{i}": "{it["tailwind"]["token"]}"')

        # Fancy grid (percentages toggle is passed in)
        render_palette_grid(items, show_percentages=show_percentages)

        st.markdown("---")
        st.markdown("### Copy-ready outputs")

        css_block = ":root{\n  " + "\n  ".join(css_vars) + "\n}"
        st.code(css_block, language="css")

        if tw_tokens:
            tw_block = "{\n  " + ",\n  ".join(tw_tokens) + "\n}"
            st.code("// Token → Tailwind match\n" + tw_block, language="json")

        tw_cfg = f"""// tailwind.config.js (example: using CSS variables as custom colors)
module.exports = {{
  theme: {{
    extend: {{
      colors: {{
        palette: {{
{"".join([f'          {i+1}: "var(--color-{i+1})",\n' for i in range(len(items))])}        }}
      }}
    }}
  }}
}};"""
        st.code(tw_cfg, language="javascript")

        st.download_button(
            "📥 Download palette as JSON",
            data=json.dumps({"palette": items}, indent=2),
            file_name="palette.json",
            mime="application/json"
        )

