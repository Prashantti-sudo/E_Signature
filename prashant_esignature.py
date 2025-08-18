import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io

st.set_page_config(page_title="PDF Signature App", page_icon="✍️")

st.title("📄 PDF Signature Application")
st.write("Upload a PDF and your signature image, then place it on the PDF.")

# Upload PDF
uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"])
# Upload signature
uploaded_sign = st.file_uploader("Upload Your Signature (PNG recommended)", type=["png", "jpg", "jpeg"])

if uploaded_pdf and uploaded_sign:
    # Load PDF
    pdf_data = uploaded_pdf.read()
    pdf = fitz.open(stream=pdf_data, filetype="pdf")

    # Load signature image
    sign_img = Image.open(uploaded_sign).convert("RGBA")

    # Resize signature
    sign_img = sign_img.resize((150, 60))

    # Convert signature to bytes for PyMuPDF
    sig_io = io.BytesIO()
    sign_img.save(sig_io, format="PNG")
    sig_bytes = sig_io.getvalue()

    # Page selection
    page_num = st.number_input("Select Page Number", min_value=1, max_value=len(pdf), value=1)
    page = pdf[page_num - 1]

    # Get page size
    rect = page.rect
    st.write(f"📐 Page Size: {rect.width} x {rect.height}")

    # Position sliders
    x_pos = st.slider("X Position", 0, int(rect.width), int(rect.width // 2))
    y_pos = st.slider("Y Position", 0, int(rect.height), int(rect.height // 2))

    # Draw signature on page
    if st.button("Apply Signature"):
        page.insert_image(
            fitz.Rect(x_pos, y_pos, x_pos + sign_img.width, y_pos + sign_img.height),
            stream=sig_bytes,
        )

        # Save signed PDF
        output_io = io.BytesIO()
        pdf.save(output_io)
        st.success("✅ Signature applied successfully!")

        # Download button
        st.download_button(
            label="⬇️ Download Signed PDF",
            data=output_io.getvalue(),
            file_name="signed_document.pdf",
            mime="application/pdf",
        )
