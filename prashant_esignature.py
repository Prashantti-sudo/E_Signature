import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import letter
import io

st.title("Drag & Drop E-Signature on PDF")

# Upload PDF
uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])

# Upload signature image
signature_image = st.file_uploader("Upload Signature Image", type=["png", "jpg", "jpeg"])

if uploaded_pdf:
    # Convert first page of PDF to image
    from pdf2image import convert_from_bytes
    pdf_bytes = uploaded_pdf.read()
    pages = convert_from_bytes(pdf_bytes)
    pdf_page_img = pages[0]
    
    # Streamlit canvas for drag & drop
    st.subheader("Drag Signature onto PDF")
    
    # Convert signature to PIL if uploaded
    if signature_image:
        signature_img = Image.open(signature_image)
        signature_img = signature_img.convert("RGBA")
    else:
        signature_img = None
    
    # Create canvas
    canvas_result = st_canvas(
        fill_color="rgba(0, 0, 0, 0)",  # Transparent background
        background_image=pdf_page_img,
        update_streamlit=True,
        height=pdf_page_img.height,
        width=pdf_page_img.width,
        drawing_mode="image" if signature_img else "freedraw",
        image_overlay=signature_img,
        key="canvas",
    )
    
    # Save PDF with signature
    if st.button("Save PDF"):
        if canvas_result.image_data is not None:
            output = Image.fromarray(canvas_result.image_data.astype("uint8"), "RGBA")
            output_pdf_path = "signed_output.pdf"
            # Convert image back to PDF
            output.convert("RGB").save(output_pdf_path)
            st.success("PDF saved successfully!")
            with open(output_pdf_path, "rb") as f:
                st.download_button("Download Signed PDF", f, file_name="signed_output.pdf", mime="application/pdf")
