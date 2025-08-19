import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_drawable_canvas import st_canvas
from pdf2image import convert_from_bytes
import io

st.title("PDF E-Signature App")

# Upload PDF
uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])

# Option to upload image signature
uploaded_signature = st.file_uploader("Or upload signature image", type=["png", "jpg", "jpeg"])

# Option to type name for signature
typed_name = st.text_input("Or type name to create signature")

# Font size
font_size = st.slider("Font Size", 30, 100, 50)

# Handle uploaded PDF
if uploaded_pdf:
    pdf_bytes = uploaded_pdf.read()
    pages = convert_from_bytes(pdf_bytes)
    pdf_image = pages[0]  # first page only
    
    # Create signature image if typed
    signature_img = None
    if typed_name:
        try:
            font_path = "AlexBrush-Regular.ttf"  # make sure this file is in project folder
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            st.warning("Font not found! Using default font.")
            font = ImageFont.load_default()
        
        signature_img = Image.new("RGBA", (400, 100), (255, 255, 255, 0))
        draw = ImageDraw.Draw(signature_img)
        draw.text((10, 10), typed_name, fill="black", font=font)
    
    # If image uploaded, use it
    if uploaded_signature:
        signature_img = Image.open(uploaded_signature).convert("RGBA")
    
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
    
    if st.button("Save Signed PDF"):
        if canvas_result.image_data is not None:
            output_image = Image.fromarray(canvas_result.image_data.astype("uint8"), "RGBA")
            output_pdf = "signed_output.pdf"
            output_image.convert("RGB").save(output_pdf)
            st.success("PDF saved successfully!")
            with open(output_pdf, "rb") as f:
                st.download_button("Download Signed PDF", f, file_name="signed_output.pdf", mime="application/pdf")
