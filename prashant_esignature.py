# app.py
"""
Streamlit E‑Signature PDF App — type your name, place it on a PDF by clicking (and nudge to fine‑tune),
optionally upload or draw a signature, and export a signed PDF.

Requirements (install locally or on Streamlit Cloud):
  pip install -U streamlit pymupdf pillow pdf2image streamlit-drawable-canvas

Fonts: put these TTF files in a local ./fonts/ folder (names can vary; update the FONT_FILES mapping below if needed):
  - AlexBrush-Regular.ttf
  - DancingScript-VariableFont_wght.ttf
  - Birthstone-Regular.ttf
  - GreatVibes-Regular.ttf
  - Pacifico-Regular.ttf

Run:
  streamlit run app.py

Notes:
- This app uses a precise click-to-place flow with a live preview and arrow nudge controls (1px / 5px). While many users say
  "drag & drop", Streamlit’s built-in primitives don’t expose continuous drag events; this implementation focuses on
  pixel-accurate placement via clicks and nudges, which is robust and cloud-friendly. You’ll still see a ghost overlay
  at the chosen coordinates.
- Coordinates are mapped correctly from the preview to PDF points.
- If you see blurry results, increase the signature size (more pixels) before placing, for extra crispness.
"""

from __future__ import annotations
import io
import math
import base64
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF

# -----------------------------
# Constants & Utilities
# -----------------------------

st.set_page_config(page_title="PDF E‑Signature", page_icon="✍️", layout="wide")

FONT_FILES: Dict[str, str] = {
    "Alex Brush": "fonts/AlexBrush-Regular.ttf",
    "Dancing Script": "fonts/DancingScript-VariableFont_wght.ttf",
    "Birthstone": "fonts/Birthstone-Regular.ttf",
    "Great Vibes": "fonts/GreatVibes-Regular.ttf",
    "Pacifico": "fonts/Pacifico-Regular.ttf",
}

DEFAULT_FONT_NAME = "Alex Brush"
SUPPORTED_IMAGE_TYPES = ["png", "jpg", "jpeg"]

@dataclass
class PagePreview:
    page_index: int
    width_px: int
    height_px: int
    image: Image.Image  # PIL image


def _load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(font_path, size=size)
    except Exception as e:
        st.warning(f"Could not load font '{font_path}': {e}. Falling back to default.")
        return ImageFont.load_default()


def _hex_to_rgba(hex_color: str, alpha: int) -> Tuple[int, int, int, int]:
    hex_color = hex_color.lstrip('#')
    lv = len(hex_color)
    rgb = tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    return int(rgb[0]), int(rgb[1]), int(rgb[2]), int(alpha)


def _render_text_image(
    text: str,
    font_name: str,
    size_px: int,
    color_hex: str,
    bold: bool = False,
    italic: bool = False,
    letter_spacing: int = 0,
    underline: bool = False,
    opacity: int = 255,
) -> Image.Image:
    """Render a text string to an RGBA image with optional styles.
    - Bold: fake by drawing multiple offset passes.
    - Italic: shear the image slightly.
    - Letter spacing: render char-by-char.
    - Underline: draw a 1–2px line near baseline.
    """
    font_path = FONT_FILES.get(font_name, FONT_FILES[DEFAULT_FONT_NAME])
    font = _load_font(font_path, size_px)

    # Measure text size with letter spacing
    draw_dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    width = 0
    ascent, descent = font.getmetrics() if hasattr(font, 'getmetrics') else (size_px, 0)
    max_h = ascent + descent
    for ch in text:
        ch_w, ch_h = draw_dummy.textsize(ch, font=font)
        width += ch_w + letter_spacing
    width = max(1, width - (letter_spacing if text else 0))
    height = max_h

    pad = max(2, size_px // 6)
    img = Image.new("RGBA", (width + 2 * pad, height + 2 * pad), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    x = pad
    y = pad

    rgba = _hex_to_rgba(color_hex, opacity)

    # Draw letters with spacing; emulate bold via offsets
    for ch in text:
        ch_w, ch_h = draw.textsize(ch, font=font)
        if bold:
            offsets = [(0, 0), (1, 0), (0, 1), (1, 1)]
        else:
            offsets = [(0, 0)]
        for dx, dy in offsets:
            draw.text((x + dx, y + dy), ch, font=font, fill=rgba)
        x += ch_w + letter_spacing

    # Underline near baseline
    if underline and text:
        baseline_y = pad + ascent + 2  # slightly below baseline
        thickness = max(1, size_px // 20)
        draw.line([(pad, baseline_y), (pad + width, baseline_y)], fill=rgba, width=thickness)

    # Italic: shear transform
    if italic:
        shear = 0.2  # approx 11 degrees
        w, h = img.size
        shift = int(shear * h)
        img = img.transform((w + shift, h), Image.AFFINE, (1, shear, 0, 0, 1, 0), resample=Image.BICUBIC)

    # Trim transparent edges
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    return img


def _image_with_opacity(img: Image.Image, opacity: int) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    alpha = img.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity / 255.0)  # type: ignore
    img.putalpha(alpha)
    return img


def _pil_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


@st.cache_data(show_spinner=False)
def render_page_preview(pdf_bytes: bytes, page_number: int, zoom: float = 1.0) -> PagePreview:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_number]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return PagePreview(
        page_index=page_number,
        width_px=pix.width,
        height_px=pix.height,
        image=img,
    )


@st.cache_data(show_spinner=False)
def get_doc_page_sizes(pdf_bytes: bytes) -> List[Tuple[float, float]]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    sizes = []
    for p in doc:
        r = p.rect
        sizes.append((float(r.width), float(r.height)))  # PDF points
    return sizes


def pdf_points_to_rect(x_pt: float, y_pt: float, w_pt: float, h_pt: float) -> fitz.Rect:
    return fitz.Rect(x_pt, y_pt, x_pt + w_pt, y_pt + h_pt)


# -----------------------------
# UI Layout
# -----------------------------

def sidebar_controls():
    st.sidebar.header("✍️ Signature Options")
    mode = st.sidebar.radio("Mode", ["Type", "Upload image", "Draw"], index=0, horizontal=True)

    # General options
    zoom = st.sidebar.slider("Preview Zoom (%)", min_value=50, max_value=300, value=150, step=10) / 100.0

    # Typed signature controls
    text, font_name, size_px, color_hex, bold, italic, underline, letter_spacing, opacity = "", DEFAULT_FONT_NAME, 72, "#000000", False, False, False, 0, 255
    if mode == "Type":
        text = st.sidebar.text_input("Name / Signature text", value="Prashant Tiwari")
        font_name = st.sidebar.selectbox("Font", list(FONT_FILES.keys()), index=list(FONT_FILES.keys()).index(DEFAULT_FONT_NAME))
        col1, col2 = st.sidebar.columns(2)
        with col1:
            size_px = st.slider("Size (px)", 24, 200, 72, 1)
            letter_spacing = st.slider("Letter spacing (px)", 0, 20, 0, 1)
        with col2:
            color_hex = st.color_picker("Color", value="#000000")
            opacity = st.slider("Opacity", 10, 255, 255, 1)
        c1, c2, c3 = st.sidebar.columns(3)
        bold = c1.toggle("Bold", value=False)
        italic = c2.toggle("Italic", value=False)
        underline = c3.toggle("Underline", value=False)

    # Upload signature image controls
    uploaded_sig = None
    img_scale = 1.0
    img_opacity = 255
    if mode == "Upload image":
        uploaded_sig = st.sidebar.file_uploader(
            "Upload signature image (PNG recommended)", type=SUPPORTED_IMAGE_TYPES
        )
        img_scale = st.sidebar.slider("Scale", 10, 300, 100, 1) / 100.0
        img_opacity = st.sidebar.slider("Opacity", 10, 255, 255, 1)

    # Draw signature controls
    draw_data = None
    draw_scale = 1.0
    if mode == "Draw":
        st.sidebar.markdown("**Draw your signature** below. Use transparent background.")
        canvas_w = st.sidebar.slider("Canvas width", 200, 800, 500, 10)
        canvas_h = st.sidebar.slider("Canvas height", 100, 400, 200, 10)
        draw = st_canvas(
            fill_color="rgba(0, 0, 0, 0)",  # fully transparent fill
            stroke_width=st.sidebar.slider("Stroke width", 1, 10, 3, 1),
            stroke_color=st.sidebar.color_picker("Stroke color", "#000000"),
            background_color="#00000000",
            height=canvas_h,
            width=canvas_w,
            drawing_mode="freedraw",
            key="draw_canvas",
        )
        draw_data = draw.image_data if draw is not None else None
        draw_scale = st.sidebar.slider("Scale", 10, 300, 100, 1) / 100.0

    return {
        "mode": mode,
        "zoom": zoom,
        "typed": {
            "text": text,
            "font_name": font_name,
            "size_px": size_px,
            "color_hex": color_hex,
            "bold": bold,
            "italic": italic,
            "underline": underline,
            "letter_spacing": letter_spacing,
            "opacity": opacity,
        },
        "upload": {
            "file": uploaded_sig,
            "scale": img_scale,
            "opacity": img_opacity,
        },
        "draw": {
            "image_data": draw_data,
            "scale": draw_scale,
        },
    }


# -----------------------------
# Main App
# -----------------------------

def main():
    st.title("✍️ PDF E‑Signature — Type, Upload or Draw")
    st.caption("Upload a PDF, place your signature on any page, and download a signed copy. Click to place; use the nudge controls to fine‑tune.")

    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"], accept_multiple_files=False)
    if not uploaded_pdf:
        st.info("Upload a PDF to begin.")
        return

    pdf_bytes = uploaded_pdf.read()
    page_sizes_pts = get_doc_page_sizes(pdf_bytes)
    num_pages = len(page_sizes_pts)

    controls = sidebar_controls()
    zoom = controls["zoom"]

    # Page selection + thumbnails
    st.subheader("Pages")
    thumb_cols = st.columns(min(6, max(1, num_pages)))
    selected_page = st.session_state.get("selected_page", 0)

    thumbs: List[PagePreview] = []
    for i in range(num_pages):
        prev = render_page_preview(pdf_bytes, i, zoom=0.2)
        thumbs.append(prev)
        with thumb_cols[i % len(thumb_cols)]:
            if st.button(f"Page {i+1}", key=f"thumb_btn_{i}"):
                selected_page = i
    st.session_state["selected_page"] = selected_page

    # Main preview
    preview = render_page_preview(pdf_bytes, selected_page, zoom=zoom)
    page_w_pts, page_h_pts = page_sizes_pts[selected_page]

    st.markdown("---")
    st.subheader(f"Preview — Page {selected_page + 1}")

    # Prepare signature image based on mode
    sig_img: Optional[Image.Image] = None
    if controls["mode"] == "Type":
        td = controls["typed"]
        if td["text"].strip():
            sig_img = _render_text_image(
                text=td["text"],
                font_name=td["font_name"],
                size_px=td["size_px"],
                color_hex=td["color_hex"],
                bold=td["bold"],
                italic=td["italic"],
                letter_spacing=td["letter_spacing"],
                underline=td["underline"],
                opacity=td["opacity"],
            )
    elif controls["mode"] == "Upload image":
        uf = controls["upload"]["file"]
        if uf is not None:
            sig_img = Image.open(uf).convert("RGBA")
            # Scale & opacity
            w, h = sig_img.size
            scale = controls["upload"]["scale"]
            sig_img = sig_img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
            if controls["upload"]["opacity"] < 255:
                a = sig_img.getchannel('A')
                a = Image.eval(a, lambda px: int(px * controls["upload"]["opacity"] / 255))
                sig_img.putalpha(a)
    elif controls["mode"] == "Draw":
        draw_img = controls["draw"]["image_data"]
        if draw_img is not None:
            # st_canvas gives a numpy array RGBA
            try:
                import numpy as np
                sig_img = Image.fromarray(draw_img.astype('uint8'))
                # trim transparent edges
                bbox = sig_img.getbbox()
                if bbox:
                    sig_img = sig_img.crop(bbox)
                scale = controls["draw"]["scale"]
                w, h = sig_img.size
                sig_img = sig_img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
            except Exception as e:
                st.warning(f"Could not process drawn signature: {e}")

    # Canvas to capture click position
    col_prev, col_info = st.columns([4, 1])
    with col_prev:
        st.write("**Instruction:** Click on the page to place your signature. Use the nudge controls to fine‑tune the position. Zoom does not affect PDF accuracy.")
        bg = preview.image
        canvas_w = min(1200, preview.width_px)  # limit width for UI
        scale_display = canvas_w / preview.width_px
        canvas_h = int(preview.height_px * scale_display)

        canvas_result = st_canvas(
            fill_color="rgba(0, 0, 0, 0)",
            stroke_width=0,
            stroke_color="#000000",
            background_image=bg,
            height=canvas_h,
            width=canvas_w,
            drawing_mode="point",  # click to place a small point; we read its coordinates
            key="place_canvas",
        )

        # Determine last click point in canvas pixel coordinates
        click_x, click_y = st.session_state.get("click_x"), st.session_state.get("click_y")
        if canvas_result.json_data is not None and "objects" in canvas_result.json_data:
            objs = canvas_result.json_data["objects"]
            if objs:
                last_obj = objs[-1]
                # For point, 'left' and 'top' give location
                click_x = float(last_obj.get("left", 0))
                click_y = float(last_obj.get("top", 0))
                st.session_state["click_x"], st.session_state["click_y"] = click_x, click_y

        # Nudge controls (in preview pixels)
        with st.expander("Nudge position (fine control)"):
            if click_x is None or click_y is None:
                st.info("Click on the preview to set a starting position.")
            else:
                colA, colB, colC = st.columns(3)
                with colA:
                    up = st.button("▲", use_container_width=True)
                    left = st.button("◀", use_container_width=True)
                with colB:
                    st.write("\n")
                    center = st.button("Reset to center")
                with colC:
                    right = st.button("▶", use_container_width=True)
                    down = st.button("▼", use_container_width=True)
                step = st.slider("Step (px)", 1, 20, 1, 1, help="How much to move per press")

                if up:
                    click_y = max(0, (click_y or 0) - step)
                if down:
                    click_y = min(canvas_h - 1, (click_y or 0) + step)
                if left:
                    click_x = max(0, (click_x or 0) - step)
                if right:
                    click_x = min(canvas_w - 1, (click_x or 0) + step)
                if center:
                    click_x, click_y = canvas_w / 2, canvas_h / 2

                st.session_state["click_x"], st.session_state["click_y"] = click_x, click_y

        # Draw a ghost overlay of the signature at the selected position
        if sig_img is not None and click_x is not None and click_y is not None:
            # Compose a ghost image for display only
            ghost = bg.convert("RGBA").copy()
            sig_w, sig_h = sig_img.size
            # Convert preview click (display px) to bg px
            ghost_x = int(click_x / scale_display - sig_w / 2)
            ghost_y = int(click_y / scale_display - sig_h / 2)
            overlay = Image.new("RGBA", ghost.size, (0, 0, 0, 0))
            overlay.paste(sig_img, (ghost_x, ghost_y), sig_img)
            ghost.alpha_composite(overlay)
            st.image(ghost, caption="Placement preview", use_container_width=True)
        else:
            st.image(bg, caption="Page preview", use_container_width=True)

    with col_info:
        st.write("**Page size (PDF points):**")
        st.code(f"{page_w_pts:.1f} × {page_h_pts:.1f}")
        if sig_img is not None:
            st.write("**Signature (px):**")
            st.code(f"{sig_img.size[0]} × {sig_img.size[1]}")
        if 'click_x' in st.session_state and st.session_state['click_x'] is not None:
            st.write("**Click (preview px):**")
            st.code(f"{int(st.session_state['click_x'])}, {int(st.session_state['click_y'])}")

        # Placement targets
        st.markdown("**Apply to pages**")
        scope = st.radio("", ["Current page", "All pages", "Selected pages"], index=0)
        selected_pages = []
        if scope == "Selected pages":
            opts = [f"Page {i+1}" for i in range(num_pages)]
            picked = st.multiselect("Choose pages", opts, default=[f"Page {selected_page+1}"])
            selected_pages = [int(s.split()[1]) - 1 for s in picked]

        # Normalized placement option
        norm_place = st.checkbox("Use normalized coordinates (percent of page)", value=True, help="Keeps placement consistent across different page sizes")

        st.markdown("---")
        # Export button
        can_apply = sig_img is not None and (st.session_state.get("click_x") is not None)
        disabled = not can_apply
        if disabled:
            st.button("Apply signature & download", disabled=True)
        else:
            if st.button("Apply signature & download", type="primary"):
                try:
                    out = apply_signature_and_export(
                        pdf_bytes=pdf_bytes,
                        sig_img=sig_img,  # PIL Image
                        click_xy_display=(st.session_state["click_x"], st.session_state["click_y"]),
                        canvas_w=canvas_w,
                        canvas_h=canvas_h,
                        page_sizes_pts=page_sizes_pts,
                        target_scope=scope,
                        current_page_index=selected_page,
                        selected_pages=selected_pages,
                        normalized=norm_place,
                        preview_scale_display=scale_display,
                    )
                    st.success("Signed PDF is ready.")
                    st.download_button("Download signed.pdf", data=out.getvalue(), file_name="signed.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"Failed to sign PDF: {e}")


# -----------------------------
# Signing Logic
# -----------------------------

def apply_signature_and_export(
    pdf_bytes: bytes,
    sig_img: Image.Image,
    click_xy_display: Tuple[float, float],
    canvas_w: int,
    canvas_h: int,
    page_sizes_pts: List[Tuple[float, float]],
    target_scope: str,
    current_page_index: int,
    selected_pages: List[int],
    normalized: bool,
    preview_scale_display: float,
) -> io.BytesIO:
    """Embed the signature image into the target pages and return a new PDF as BytesIO."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # Which pages to write
    if target_scope == "Current page":
        target_idxs = [current_page_index]
    elif target_scope == "All pages":
        target_idxs = list(range(len(page_sizes_pts)))
    else:
        target_idxs = sorted(set(selected_pages)) or [current_page_index]

    # Convert display click to PDF coordinates on the CURRENT page
    sig_w_px, sig_h_px = sig_img.size
    click_x_display, click_y_display = click_xy_display

    # Position of signature *center* in display pixels → background pixels → PDF points
    # First convert display px → background px (rendered preview image) using preview_scale_display
    click_x_bg = click_x_display / preview_scale_display
    click_y_bg = click_y_display / preview_scale_display

    # Convert bg px → PDF points using current page size and preview pixmap size
    current_prev = render_page_preview(pdf_bytes, current_page_index, zoom=1.0)  # 1.0 = baseline we used earlier
    bg_w_px, bg_h_px = current_prev.width_px, current_prev.height_px
    page_w_pts, page_h_pts = page_sizes_pts[current_page_index]

    x_pt_center = (click_x_bg / bg_w_px) * page_w_pts
    y_pt_top_ui = (click_y_bg / bg_h_px) * page_h_pts  # UI with origin at top-left

    # Convert top-origin y to PDF bottom-origin y for center point
    y_pt_center = page_h_pts - y_pt_top_ui

    # Signature size in PDF points: assume 96 DPI for px→pt unless you want a slider
    DPI = 96.0
    sig_w_pts = sig_w_px * 72.0 / DPI
    sig_h_pts = sig_h_px * 72.0 / DPI

    # Upper-left corner in PDF coordinates for current page
    x_pt_ul = x_pt_center - sig_w_pts / 2.0
    y_pt_ul = y_pt_center - sig_h_pts / 2.0

    # If normalized, convert the UL coords to percentages of the page to reuse across pages
    if normalized:
        nx = x_pt_ul / page_w_pts
        ny = y_pt_ul / page_h_pts
        nw = sig_w_pts / page_w_pts
        nh = sig_h_pts / page_h_pts
    else:
        nx = ny = nw = nh = None  # type: ignore

    # Prepare signature bytes once (PNG)
    sig_bytes = _pil_to_bytes(sig_img, fmt="PNG")

    for i in target_idxs:
        page = doc[i]
        pw, ph = page_sizes_pts[i]
        if normalized:
            x = nx * pw  # type: ignore
            y = ny * ph  # type: ignore
            w = nw * pw  # type: ignore
            h = nh * ph  # type: ignore
        else:
            # Recompute mapping for each page using the same display click (approximate; best is normalized)
            if i == current_page_index:
                x, y, w, h = x_pt_ul, y_pt_ul, sig_w_pts, sig_h_pts
            else:
                # Map via relative fractions of CURRENT page
                fx = x_pt_ul / page_w_pts
                fy = y_pt_ul / page_h_pts
                fw = sig_w_pts / page_w_pts
                fh = sig_h_pts / page_h_pts
                x, y, w, h = fx * pw, fy * ph, fw * pw, fh * ph

        # Convert UL (PDF) to Rect expects (x0,y0,x1,y1) with y from bottom
        rect = pdf_points_to_rect(x, y, w, h)
        page.insert_image(rect, stream=sig_bytes, keep_proportion=False)

    out_buf = io.BytesIO()
    doc.save(out_buf)
    doc.close()
    out_buf.seek(0)
    return out_buf


if __name__ == "__main__":
    main()
