
import io
import base64
from dataclasses import dataclass
from typing import Optional, Tuple

import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import numpy as np

st.set_page_config(page_title="Drag & Drop E‑Signature", layout="wide")

# --------------------------
# Helpers
# --------------------------
@dataclass
class PdfPageImage:
    page_index: int
    width: int
    height: int
    image: Image.Image  # RGB page image for background


@st.cache_data(show_spinner=False)
def pdf_to_images(file_bytes: bytes, zoom: float = 2.0):
    """Rasterize each page of a PDF to a PIL.Image using PyMuPDF (no poppler dependency)."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []
    for i in range(len(doc)):
        page = doc[i]
        mat = fitz.Matrix(zoom, zoom)  # upscale for clarity
        pix = page.get_pixmap(matrix=mat, alpha=False)  # RGB
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        pages.append(PdfPageImage(page_index=i, width=pix.width, height=pix.height, image=img))
    return pages


def make_canvas_json_with_text(
    text: str,
    canvas_w: int,
    canvas_h: int,
    font_family: str = "DejaVu Sans",
    font_size: int = 48,
) -> dict:
    # Create a Fabric.js JSON with a draggable i-text object (works with streamlit-drawable-canvas)
    # Place near bottom by default
    left = canvas_w * 0.3
    top = canvas_h * 0.8
    return {
        "version": "5.2.4",
        "objects": [
            {
                "type": "i-text",
                "left": left,
                "top": top,
                "text": text,
                "fontFamily": font_family,
                "fontSize": font_size,
                "fill": "#000000",
                "scaleX": 1,
                "scaleY": 1,
                "editable": True,
            }
        ],
    }


def pil_text_signature_png(
    text: str,
    font_bytes: Optional[bytes],
    font_size: int,
    underline: bool,
    padding: int = 10,
) -> Image.Image:
    """Render text onto a transparent PNG. Use provided TTF bytes if any, else fallback."""
    try:
        if font_bytes:
            font = ImageFont.truetype(io.BytesIO(font_bytes), size=font_size)
        else:
            # Fallback to a commonly-available DejaVu font bundled with Pillow
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", size=font_size)
            except Exception:
                font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # Determine size
    dummy = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    img = Image.new("RGBA", (text_w + 2 * padding, text_h + 2 * padding), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((padding, padding), text, font=font, fill=(0, 0, 0, 255))

    if underline:
        y = padding + text_h + 4
        draw.line((padding, y, padding + text_w, y), fill=(0, 0, 0, 255), width=max(2, font_size // 15))

    return img


def transparent_from_canvas_rgba(arr: np.ndarray) -> Image.Image:
    """Convert the canvas image_data RGBA into a transparent PNG (keep only drawn strokes)."""
    # If background is transparent, areas with all zeros alpha are background; keep others
    # Ensure we have 4 channels
    if arr.shape[2] == 3:
        # Add opaque alpha if missing
        alpha = np.full((arr.shape[0], arr.shape[1], 1), 255, dtype=np.uint8)
        arr = np.concatenate([arr, alpha], axis=2)

    img = Image.fromarray(arr.astype("uint8"), mode="RGBA")
    return img


def insert_png_on_pdf(
    pdf_bytes: bytes,
    page_index: int,
    png_img: Image.Image,
    x: float,
    y: float,
    target_width: Optional[float],
) -> bytes:
    """Insert a transparent PNG onto a PDF page at (x,y) in PDF pixel space (top-left origin).
       If target_width is provided, scale the image to that width (preserving aspect)."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_index]
    # Convert PIL image to PNG bytes
    buf = io.BytesIO()
    png_img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    # Size in PDF space
    img = fitz.Pixmap(png_bytes)
    img_w = img.width
    img_h = img.height

    if target_width is not None and target_width > 0:
        scale = target_width / img_w
        img_w = target_width
        img_h = int(img_h * scale)

    rect = fitz.Rect(x, y, x + img_w, y + img_h)
    page.insert_image(rect, stream=png_bytes, keep_proportion=True, overlay=True)

    out = io.BytesIO()
    doc.save(out)
    doc.close()
    return out.getvalue()


def download_button(data: bytes, filename: str, label: str):
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{label}</a>'
    st.markdown(href, unsafe_allow_html=True)


# --------------------------
# UI
# --------------------------
st.title("🖊️ Drag & Drop E‑Signature for PDF")
st.caption("1) Upload PDF → 2) Type or draw signature → 3) Drag/position → 4) Save")

uploaded_pdf = st.file_uploader("1) Select a PDF file", type=["pdf"])

if not uploaded_pdf:
    st.info("Upload a PDF to get started.")
    st.stop()

# Convert to images for preview/canvas backgrounds
pages = pdf_to_images(uploaded_pdf.getvalue(), zoom=2.0)
page_nums = [f"Page {p.page_index + 1}" for p in pages]
colA, colB = st.columns([1, 2], gap="large")

with colA:
    page_choice = st.selectbox("Choose page to sign", page_nums, index=0)
    page_ix = int(page_choice.split()[-1]) - 1
    selected_page = pages[page_ix]

    st.image(selected_page.image, caption=f"Preview: {page_choice}", use_column_width=True)

# Signature options
with colB:
    st.subheader("2) Create your signature")
    tab_text, tab_draw = st.tabs(["Type signature", "Draw signature"])

    signature_png: Optional[Image.Image] = None
    sig_mode = None

    with tab_text:
        name = st.text_input("Your name", value="Your Name")
        font_size = st.slider("Font size", min_value=24, max_value=150, value=64, step=2)
        underline = st.checkbox("Underline", value=False)
        font_upload = st.file_uploader("Optional: Upload a .ttf font", type=["ttf"], key="font")

        # Build a Fabric canvas with a draggable text object
        canvas_w, canvas_h = selected_page.width, selected_page.height
        init_json = make_canvas_json_with_text(
            text=name, canvas_w=canvas_w, canvas_h=canvas_h, font_size=font_size
        )

        st.write("3) Drag the text on the canvas to position it, then click **Save to PDF**.")
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",  # transparent
            background_image=selected_page.image,
            update_streamlit=True,
            width=canvas_w,
            height=canvas_h,
            drawing_mode="transform",  # enables moving/scaling existing objects
            initial_drawing=init_json,
            key=f"canvas_text_{page_ix}_{name}_{font_size}_{underline}",
        )

        # Render the signature PNG now (we'll place it later using the object's coords)
        font_bytes = font_upload.read() if font_upload else None
        signature_png = pil_text_signature_png(name, font_bytes, font_size, underline)
        sig_mode = "text"

    with tab_draw:
        st.write("Use the pen to draw your signature, drag/scale it, then **Save to PDF**.")
        stroke_w = st.slider("Stroke width", 1, 12, 4)
        canvas_w, canvas_h = selected_page.width, selected_page.height

        draw_canvas = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",  # transparent background
            background_image=selected_page.image,
            update_streamlit=True,
            width=canvas_w,
            height=canvas_h,
            drawing_mode="freedraw",
            stroke_width=stroke_w,
            stroke_color="#000000",
            key=f"canvas_draw_{page_ix}",
        )

    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col1:
        save_btn = st.button("4) Save to PDF", type="primary", use_container_width=True)

    if save_btn:
        # Determine placement based on which tab is active (by checking the last interacted canvas)
        active_text = canvas_result.json_data if 'canvas_result' in locals() else None
        active_draw = draw_canvas if 'draw_canvas' in locals() else None

        if sig_mode == "text" and active_text and "objects" in active_text and len(active_text["objects"]) > 0:
            # Find the i-text object
            obj = None
            for o in active_text["objects"]:
                if o.get("type", "").endswith("text"):
                    obj = o
                    break
            if obj is None:
                st.error("Couldn't find the text object on the canvas. Try again.")
                st.stop()

            left = float(obj.get("left", 0))
            top = float(obj.get("top", 0))
            scale_x = float(obj.get("scaleX", 1.0))
            # We will scale the rendered PNG width according to the object scaleX
            target_width = signature_png.width * scale_x

            # (x, y) is top-left in canvas pixel space, which matches PDF pixel space from our rasterization
            new_pdf = insert_png_on_pdf(
                uploaded_pdf.getvalue(),
                page_index=page_ix,
                png_img=signature_png,
                x=left,
                y=top,
                target_width=target_width,
            )
            st.success("Signature placed and PDF saved!")
            st.download_button("Download signed PDF", data=new_pdf, file_name="signed.pdf")

        elif active_draw and active_draw.image_data is not None:
            # Extract just the drawn strokes as transparent PNG by subtracting background (already transparent)
            rgba = active_draw.image_data
            if isinstance(rgba, np.ndarray):
                drawn_img = transparent_from_canvas_rgba(rgba)
            else:
                st.error("Unexpected canvas image format.")
                st.stop()

            # For drawn signatures, we need the bounding box of non-transparent pixels to derive a minimal image and position.
            arr = np.array(drawn_img)
            alpha = arr[:, :, 3]
            ys, xs = np.where(alpha > 0)
            if len(xs) == 0 or len(ys) == 0:
                st.error("No drawing detected. Please draw your signature.")
                st.stop()

            min_x, max_x = xs.min(), xs.max()
            min_y, max_y = ys.min(), ys.max()
            cropped = drawn_img.crop((min_x, min_y, max_x + 1, max_y + 1))

            # Insert at that same bbox location on the PDF
            new_pdf = insert_png_on_pdf(
                uploaded_pdf.getvalue(),
                page_index=page_ix,
                png_img=cropped,
                x=float(min_x),
                y=float(min_y),
                target_width=None,
            )
            st.success("Signature placed and PDF saved!")
            st.download_button("Download signed PDF", data=new_pdf, file_name="signed.pdf")

        else:
            st.error("Please create a signature (type or draw) before saving.")
