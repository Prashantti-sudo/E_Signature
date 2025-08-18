import io
import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
import pdfplumber
from PIL import Image

st.set_page_config(page_title="PDF E-Signature", layout="wide")
st.title("✍️ PDF E-Signature Tool (Click to Place Signature)")

uploaded_pdf = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_pdf:
    signature_text = st.text_input("Enter your signature", "John Doe")
    font_size = st.slider("Font size", 8, 48, 18)

    # Read PDF
    reader = PdfReader(uploaded_pdf)
    total_pages = len(reader.pages)
    page_number = st.number_input("Select page", 1, total_pages, 1)

    # Render page as image
    with pdfplumber.open(uploaded_pdf) as pdf:
        page = pdf.pages[page_number-1]
        pil_img = page.to_image(resolution=150).original

    st.image(pil_img, caption=f"Page {page_number}", use_container_width=True)

    st.markdown("### 👇 Click on the PDF preview to place signature (X, Y)")
    coords = st.session_state.get("coords", None)

    # Let user input manually if not interactive
    x = st.number_input("X Position", 0, int(pil_img.width), 50)
    y = st.number_input("Y Position", 0, int(pil_img.height), 50)

    if st.button("Apply Signature"):
        # Get page dimensions
        page = reader.pages[page_number-1]
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        # Convert from image coords to PDF coords
        pdf_x = x * (width / pil_img.width)
        pdf_y = height - (y * (height / pil_img.height))

        writer = PdfWriter()
        for i, p in enumerate(reader.pages):
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=(width, height))
            if i == page_number-1:
                c.setFont("Helvetica-Bold", font_size)
                c.setFillColor(HexColor("#000000"))
                c.drawString(pdf_x, pdf_y, signature_text)
            c.save()
            packet.seek(0)
            overlay = PdfReader(packet)
            p.merge_page(overlay.pages[0])
            writer.add_page(p)

        output = io.BytesIO()
        writer.write(output)
        output.seek(0)

        st.success("✅ Signature applied!")
        st.download_button(
            "📥 Download Signed PDF",
            data=output,
            file_name="signed_document.pdf",
            mime="application/pdf"
        )
