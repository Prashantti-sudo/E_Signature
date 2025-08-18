import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import io
import os

st.set_page_config(page_title="Typed E-Signature App", page_icon="✍️")

st.title("📄 Typed E-Signature Application")
st.write("Upload a PDF/Image, type your name, and choose a signature style.")

# Upload file
uploaded_file = st.file_uploader("Upload a PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

# User types name
user_name = st.text_input("✍️ Enter Your Name for Signature", "John Doe")

# Define fonts (you can add .ttf fonts in the same folder)
font_styles = {
    "Elegant": "arial.ttf",
    "Bold": "arialbd.ttf",
    "Cursive": "times.ttf"
}

if uploaded_file and user_name:
    file_type = uploaded_file.type
    
    if "pdf" in file_type:
        # Load first page of PDF as image preview
        pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        page = pdf[0]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    else:
        # Load image
        img = Image.open(uploaded_file).convert("RGB")

    st.image(img, caption="Uploaded Document Preview", use_container_width=True)

    st.write("👉 Choose a signature style:")

    # Generate signature previews
    sig_images = {}
    for style, font_path in font_styles.items():
        try:
            font = ImageFont.truetype(font_path, 50)
        except:
            font = ImageFont.load_default()

        sig_img = Image.new("RGBA", (400, 100), (255, 255, 255, 0))
        draw = ImageDraw.Draw(sig_img)
        draw.text((10, 10), user_name, font=font, fill="black")
        sig_images[style] = sig_img

    # Show signature options
    selected_style = st.radio("Select Signature Style", list(sig_images.keys()))
    st.image(sig_images[selected_style], caption=f"Preview: {selected_style}")

    # Position sliders
    x_pos = st.slider("X Position", 0, img.width, img.width - 200)
    y_pos = st.slider("Y Position", 0, img.height, img.height - 100)

    if st.button("Apply Signature"):
        doc_img = img.copy()
        sig_img = sig_images[selected_style]
        doc_img.paste(sig_img, (x_pos, y_pos), sig_img)

        st.image(doc_img, caption="Signed Document", use_container_width=True)

        # Save and download
        buf = io.BytesIO()
        doc_img.save(buf, format="PNG")
        st.download_button(
            label="⬇️ Download Signed Document",
            data=buf.getvalue(),
            file_name="signed_document.png",
            mime="image/png"
        )
