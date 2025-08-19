import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import fitz  # PyMuPDF
import io

st.title("E-Signature PDF Tool (No Poppler Needed)")

# Upload PDF
uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_pdf is not None:
    # Open PDF with PyMuPDF
    pdf_document = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")

    # Show first page as preview
    page = pdf_document[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # zoom for better quality
    img_bytes = pix.tobytes("png")
    st.image(img_bytes, caption="Page 1 Preview")

    # Signature canvas
    st.subheader("Draw your signature below")
    canvas_result = st_canvas(
        fill_color="rgba(0,0,0,0)",  
        stroke_width=3,
        stroke_color="black",
        background_color="white",
        width=400,
        height=150,
        drawing_mode="freedraw",
        key="canvas",
    )

    if st.button("Place Signature and Download PDF"):
        if canvas_result.image_data is not None:
            # Convert signature to image
            sig_img = Image.fromarray(canvas_result.image_data.astype("uint8"), "RGBA")
            sig_img = sig_img.convert("RGB")
            
            # Save signature temporarily
            sig_bytes = io.BytesIO()
            sig_img.save(sig_bytes, format="PNG")
            sig_bytes.seek(0)

            # Insert signature into first page
            rect = fitz.Rect(100, 500, 300, 600)  # position of signature
            page.insert_image(rect, stream=sig_bytes.getvalue())

            # Save modified PDF
            output_pdf = io.BytesIO()
            pdf_document.save(output_pdf)
            output_pdf.seek(0)

            st.success("✅ Signature added to PDF!")
            st.download_button(
                "Download Signed PDF",
                output_pdf,
                file_name="signed_output.pdf",
                mime="application/pdf",
            )
