import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
import io
import os

st.set_page_config(page_title="Typed Signature App", page_icon="✍️")

st.title("📄 Typed E-Signature Application")
st.write("Upload a PDF/Image, type your name, and place your signature.")

# Upload document
uploaded_file = st.file_uploader("Upload a PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

# User input name
user_name = st.text_input("✍️ Enter Your Name for Signature", "John Doe")

# Font options (add .ttf in project folder)
font_options = {
    "Pacifico": "Pacifico.ttf",
    "Great Vibes": "GreatVibes-Regular.ttf",
    "Dancing Script": "DancingScript-Regular.ttf",
    "Arial": "arial.ttf",
    "Times New Roman": "times.ttf"
}

if uploaded_file and user_name:
    # Handle PDF / Image
    file_type = uploaded_file.type
    if "pdf" in file_type:
        pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        page = pdf[0]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    else:
        img = Image.open(uploaded_file).convert("RGB")

    st.image(img, caption="📄 Uploaded Document", use_container_width=True)

    # Generate multiple signature styles
    st.subheader("👉 Choose Signature Style")
    previews = {}
    for style, font_path in font_options.items():
        try:
            font = ImageFont.truetype(font_path, 80)  # Bigger text
        except:
            font = ImageFont.load_default()

        sig_img = Image.new("RGBA", (500, 150), (255, 255, 255, 0))
        draw = ImageDraw.Draw(sig_img)
        draw.text((10, 10), user_name, font=font, fill="black")
        previews[style] = sig_img

    # Display previews in columns
    cols = st.columns(len(previews))
    for i, (style, img_sig) in enumerate(previews.items()):
        with cols[i]:
            st.image(img_sig, caption=style)
    selected_style = st.selectbox("Select your signature style", list(previews.keys()))

    # Use canvas to drag & drop
    st.subheader("✍️ Drag & Place Your Signature")
    canvas_result = st_canvas(
        fill_color="rgba(255,255,255,0)",
        stroke_width=0,
        stroke_color="rgba(0,0,0,0)",
