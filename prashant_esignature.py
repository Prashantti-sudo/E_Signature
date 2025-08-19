import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_drawable_canvas import st_canvas
from pdf2image import convert_from_bytes, exceptions as pdf2image_exceptions
import os

st.set_page_config(layout="wide")
st.title("PDF E-Signature App")

# --- Upload PDF ---
uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])

# --- Upload signature image ---
uploaded_signature = st.file_uploader("Or upload signature image", type=["png", "jpg", "jpeg"])

# --- Typed name signature ---
typed_name = st.text_input("Or type name to create signature")
font_size = st.slider("Font Size", 30, 100, 50)

# --- Process PDF ---
if uploaded_pdf:
    pdf_bytes = uploaded_pdf.read()
    
    try:
        # Convert PDF first page to image
        pages = convert_from_bytes(pdf_bytes)
        pdf_image = pages[0]
    except pdf2image_exceptions.PDFInfoNotInstalledError:
        st.error("""
        Poppler is not installed or not found in PATH!  
        Please install Poppler:
        - **Linux:** `sudo apt install poppler-utils`
        - **Mac:** `brew install poppler`
        - **Windows:** Download from [Poppler Windows](https://github.com/oschwartz10612/poppler-windows/releases/) and add `bin` folder to PATH.
        """)
        st.stop()

    # --- Create signature image from typed name ---
    signature_img = None
    if typed_name:
        try:
            font_path = os.path.join("fonts", "AlexBrush-Regular.ttf")
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            st.warning("Font not found! Using default font.")
            font = ImageFont.load_default()

        signature_img = Image.new("RGBA", (400, 100), (255, 255, 255, 0))
        draw = ImageDraw.Draw(signature_img)
        draw.text((10, 10), typed_name, fill="black", font=font)

    # --- Use uploaded signature image if provided ---
    if uploaded_signature:
        signature_img = Image.open(uploaded_signature).convert("RGBA")

    # --- Streamlit canvas for drag & drop ---
    st.subheader("Drag signature onto PDF")
    canvas_result = st_canvas(
        fill_color="rgba(0, 0, 0, 0)",
        background_image=pdf_image,
        width=pdf_image.width,
        height=pdf_image.height,
        drawing_mode="image" if signature_img else "freedraw",
        image_overlay=signature_img,
        key="canvas"
    )

    # --- Save final PDF ---
    if st.button("Save Signed PDF"):
        if canvas_result.image_data is not None:
            output_image = Image.fromarray(canvas_result.image_data.astype("uint8"), "RGBA")
            output_pdf = "signed_output.pdf"  # Fixed unterminated string
            output_image.convert("RGB").save(output_pdf)
            st.success("PDF saved successfully!")
            with open(output_pdf, "rb") as f:
                st.download_button("Download Signed PDF", f, file_name="signed_output.pdf", mime="application/pdf")
