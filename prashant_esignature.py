import io
import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

st.set_page_config(page_title="PDF E-Signature", layout="wide")
st.title("✍️ PDF E-Signature Tool (Poppler-Free)")

uploaded_pdf = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_pdf:
    signature_text = st.text_input("Enter your signature", "John Doe")
    font_size = st.slider("Font size", 8, 48, 18)

    # Page selection
    reader = PdfReader(uploaded_pdf)
    total_pages = len(reader.pages)
    page_number = st.number_input("Select page to sign", 1, total_pages, 1)

    # X, Y position
    page = reader.pages[page_number-1]
    width = float(page.mediabox.width)
    height = float(page.mediabox.height)

    x = st.slider("X Position", 0, int(width), int(width/4))
    y = st.slider("Y Position", 0, int(height), int(height/4))

    if st.button("Apply Signature"):
        writer = PdfWriter()
        for i, p in enumerate(reader.pages):
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=(width, height))
            if i == page_number-1:
                c.setFont("Helvetica-Bold", font_size)
                c.setFillColor(HexColor("#000000"))
                c.drawString(x, y, signature_text)
            c.save()
            packet.seek(0)
            overlay = PdfReader(packet)
            p.merge_page(overlay.pages[0])
            writer.add_page(p)

        output = io.BytesIO()
        writer.write(output)
        output.seek(0)

        st.success("✅ Signature applied successfully!")
        st.download_button(
            label="📥 Download Signed PDF",
            data=output,
            file_name="signed_document.pdf",
            mime="application/pdf"
        )
