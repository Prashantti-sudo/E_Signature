import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import io
import os

st.set_page_config(page_title="E-Signature on Documents", page_icon="✍️")

st.title("📄 E-Signature Application")
st.write("Upload a file and add your typed digital signature.")

# Upload file
uploaded_file = st.file_uploader("Upload a PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

# User types name for signature
user_name = st.text_input("✍️ Enter Your Name for Signature", "John Doe")

# Font choices (you can add more .ttf fonts in same folder)
fonts = {
    "Elegant": "arial.ttf",   # default system font
    "Cursive": "times.ttf",   # replace with cursive font if available
    "Bold": "arialbd.ttf"     # bold font
}

font_choice = st.selectbox("Choose Signature Font", list(fonts.keys()))

if uploaded_file and user_name:
    file_type = uploaded_file.type
    
    if "pdf" in file_type:
        # Load first page of PDF as preview
        pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        page = pdf[0]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    else:
        # Load image file
        img = Image.open(uploaded_file).convert("RGB")

    st.image(img, caption="Uploaded Document Preview", use_container_width=True)

    # Generate signature image
    try:
        font = ImageFont.truetype(fonts[font_choice], 50)  # font size 50
    except:
        font = ImageFont.load_default()

    sig_img = Image.new("RGBA", (400, 100), (255, 255, 255, 0))  # transparent bg
    draw = ImageDraw.Draw(sig_img)
    draw.text((10, 10), user_name, font=font, fill="black")

    st.image(sig_img, caption="Generated Signature Preview")

    st.write("👉 Adjust position of signature on document:")

    # Sliders for position
    x_pos = st.slider("X Position", 0, img.width, img.width - 200)
    y_pos = st.slider("Y Position", 0, img.height, img.height - 100)

    if st.button("Apply Signature"):
        doc_img = img.copy()
        doc_img.paste(sig_img, (x_pos, y_pos), sig_img)

        st.image(doc_img, caption="Signed Document", use_container_width=True)

        # Save final signed document
        buf = io.BytesIO()
        doc_img.save(buf, format="PNG")
        st.download_button(
            label="⬇️ Download Signed Document",
            data=buf.getvalue(),
            file_name="signed_document.png",
            mime="image/png"
        )
