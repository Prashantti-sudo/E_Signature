import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from io import BytesIO

st.set_page_config(page_title="PDF E-Signature App", layout="centered")

st.title("📄✍️ PDF E-Signature App")

st.write("Upload a PDF, type your signature, and download the signed version.")

# Upload PDF
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    st.success("✅ PDF uploaded successfully!")

    # Signature text input
    signature_text = st.text_input("Enter your signature text", "John Doe")
    x_pos = st.slider("X Position (in inches)", 0.5, 6.0, 2.0, 0.1)
    y_pos = st.slider("Y Position (in inches)", 0.5, 10.0, 1.0, 0.1)

    if st.button("Apply Signature"):
        # Create a temporary PDF with signature
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.setFont("Helvetica-Bold", 18)
        can.drawString(x_pos * inch, y_pos * inch, signature_text)
        can.save()

        packet.seek(0)
        signature_pdf = PdfReader(packet)

        # Read uploaded PDF
        reader = PdfReader(uploaded_file)
        writer = PdfWriter()

        # Merge signature on first page
        for i, page in enumerate(reader.pages):
            if i == 0:
                page.merge_page(signature_pdf.pages[0])
            writer.add_page(page)

        # Output signed PDF
        output = BytesIO()
        writer.write(output)
        output.seek(0)

        st.success("✅ Signature added successfully!")

        st.download_button(
            label="📥 Download Signed PDF",
            data=output,
            file_name="signed_document.pdf",
            mime="application/pdf"
        )
