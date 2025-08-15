# core/ui.py
from __future__ import annotations
from typing import List, Dict, Any
import streamlit as st
import streamlit.components.v1 as components

def wcag_class(ratio: float) -> str:
    if ratio >= 7.0: return "ok"
    if ratio >= 4.5: return "ok"
    if ratio >= 3.0: return "warn"
    return "fail"

def wcag_label(ratio: float) -> str:
    if ratio >= 7.0: return "AAA"
    if ratio >= 4.5: return "AA"
    if ratio >= 3.0: return "AA (Large)"
    return "N/A"

def render_palette_grid(items: List[Dict[str, Any]], show_percentages: bool = True):
    """
    items: [
      {
        index, hex, rgb=(r,g,b), weight, tailwind={token,hex,deltaE}|None,
        ideal_text: "rgb(...)", cr_black, cr_white, wcag_label
      }, ...
    ]
    """
    # Build HTML with CSS + JS INSIDE the iframe so styles/scripts apply.
    rows = []
    for it in items:
        hexv = it["hex"].upper()
        rgb = it["rgb"]
        fg = it["ideal_text"]
        pct = f"{it['weight']*100:.1f}%" if show_percentages else ""
        tw = it.get("tailwind")
        contrast_val = max(it["cr_black"], it["cr_white"])
        contrast_txt = f"{contrast_val:.2f} ({wcag_label(contrast_val)})"
        cls = wcag_class(contrast_val)

        tw_badge = tw_btn = ""
        if tw:
            tw_badge = f'<span class="badge">{tw["token"]}</span>'
            tw_btn = f'<button class="btn" onclick="copyText(\'{tw["token"]}\')">Copy TW</button>'

        rows.append(f"""
        <div class="card">
          <div class="swatch" style="background:{hexv};"></div>
          <div class="body" style="color:{fg}">
            <div class="row">
              <strong>#{it["index"]} — {hexv}</strong>
              <span class="meta">{pct}</span>
            </div>
            <div class="row">
              <span class="badge">rgb({rgb[0]}, {rgb[1]}, {rgb[2]})</span>
              {tw_badge}
            </div>
            <div class="row">
              <button class="btn" onclick="copyText('{hexv}')">Copy HEX</button>
              <button class="btn" onclick="copyText('rgb({rgb[0]}, {rgb[1]}, {rgb[2]})')">Copy RGB</button>
              {tw_btn}
            </div>
            <div class="row small">
              <span class="{cls}">Contrast: {contrast_txt}</span>
            </div>
          </div>
        </div>
        """)

    html = f"""
    <html>
    <head>
      <meta charset="utf-8" />
      <style>
        :root {{
          --surface: rgba(255,255,255,.7);
          --border: rgba(0,0,0,.08);
          --shadow1: 0 8px 24px rgba(0,0,0,.08);
          --shadow2: 0 12px 32px rgba(0,0,0,.12);
        }}
        html,body {{
          margin:0; padding:0;
          background: transparent;  /* avoids dark iframe bg */
          font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
          color: #111;
        }}
        .grid {{
          display:grid; gap:16px;
          grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
          padding: 4px;
        }}
        .card {{
          border:1px solid var(--border);
          border-radius:16px;
          overflow:hidden;
          background:var(--surface);
          backdrop-filter: blur(6px);
          box-shadow: var(--shadow1);
          transition: transform .15s ease, box-shadow .15s ease;
        }}
        .card:hover {{ transform: translateY(-2px); box-shadow: var(--shadow2); }}
        .swatch {{ height: 90px; }}
        .body {{ padding:12px 14px; font-size:14px; }}
        .row {{ display:flex; align-items:center; justify-content:space-between; margin:6px 0; gap:8px; }}
        .meta {{ opacity:.75 }}
        .badge {{
          font-size:12px; padding:2px 8px; border-radius:999px;
          border:1px solid var(--border); background:rgba(255,255,255,.6);
        }}
        .btn {{
          font-size:12px; padding:4px 8px; border-radius:8px;
          border:1px solid rgba(0,0,0,.12); background:rgba(255,255,255,.85);
          cursor:pointer;
        }}
        .btn:active {{ transform: scale(.98); }}
        .small {{ font-size:12px; opacity:.9 }}
        .ok {{ color:#0a7a2a; }}
        .warn {{ color:#b36b00; }}
        .fail {{ color:#b00020; }}
      </style>
    </head>
    <body>
      <div class="grid">
        {''.join(rows)}
      </div>
      <script>
        function copyText(txt) {{
          navigator.clipboard.writeText(txt).catch(()=>{{
            // fallback
            const ta = document.createElement('textarea');
            ta.value = txt; document.body.appendChild(ta); ta.select();
            try {{ document.execCommand('copy'); }} catch(e) {{}}
            document.body.removeChild(ta);
          }});
        }}
      </script>
    </body>
    </html>
    """
    # Taller height for many cards; enable scrolling.
    components.html(html, height=680, scrolling=True)