import io
import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor

st.set_page_config(page_title="PDF E-Signature", layout="centered")
st.title("✍️ PDF E-Signature Tool")

# Upload PDF
uploaded_pdf = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_pdf:
    reader = PdfReader(uploaded_pdf)

    # Signature input
    signature_text = st.text_input("Enter your signature", "John Doe")
    font_size = st.slider("Font size", 8, 48, 18)
    x_in = st.slider("X position (inches)", 0.5, 6.0, 2.0, 0.1)
    y_in = st.slider("Y position (inches)", 0.5, 10.0, 1.0, 0.1)

    if st.button("Apply Signature"):
        writer = PdfWriter()

        for page in reader.pages:
            # Create a temporary canvas for signature
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=(float(page.mediabox.width),
                                                float(page.mediabox.height)))
            c.setFont("Helvetica-Bold", font_size)
            c.setFillColor(HexColor("#000000"))  # black color
            c.drawString(x_in * inch, y_in * inch, signature_text)
            c.save()

            packet.seek(0)
            overlay = PdfReader(packet)

            # Merge signature with page
            page.merge_page(overlay.pages[0])
            writer.add_page(page)

        # Save signed PDF
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
