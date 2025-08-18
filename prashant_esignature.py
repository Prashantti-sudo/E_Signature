import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

def create_signature_pdf(signature_text, width, height, margin_x=50, margin_y=30):
    """
    Creates a temporary PDF with signature text at bottom-right
    """
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    can.setFont("Helvetica-Bold", 12)
    can.drawRightString(width - margin_x, margin_y, signature_text)  # bottom-right
    can.save()
    packet.seek(0)
    return PdfReader(packet)

def add_signature_to_pdf(uploaded_file, signature_text):
    reader = PdfReader(uploaded_file)
    writer = PdfWriter()

    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        # create signature layer
        sig_pdf = create_signature_pdf(signature_text, width, height)
        sig_page = sig_pdf.pages[0]

        # merge signature on page
        page.merge_page(sig_page)
        writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output


# ---------------- STREAMLIT UI ----------------
st.title("📄 PDF E-Signature App")

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])
signature_text = st.text_input("Enter your Signature Text (Name)", "")

if uploaded_file and signature_text:
    if st.button("Add Signature"):
        signed_pdf = add_signature_to_pdf(uploaded_file, signature_text)

        st.success("✅ Signature added at bottom-right corner!")
        st.download_button(
            label="📥 Download Signed PDF",
            data=signed_pdf,
            file_name="signed_document.pdf",
            mime="application/pdf"
        )
