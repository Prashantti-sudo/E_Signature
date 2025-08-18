import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import io
import os

st.set_page_config(page_title="E-Signature on Documents", page_icon="✍️")

st.title("📄 E-Signature Application")
st.write("Upload a file and sign it digitally.")

# Upload file
uploaded_file = st.file_uploader("Upload a PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
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

    st.write("✍️ Choose how you want to sign:")

    # Option to choose signature method
    sign_method = st.radio("Se_
