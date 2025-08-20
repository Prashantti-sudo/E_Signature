import streamlit as st
import io
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def add_signature(input_pdf, output_pdf, signature_text, x, y, page_num=0):
    # Create a PDF with the signature text
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica-Bold", 18)
    can.drawString(x, y, signature_text)
    can.save()

    # Move to start
    packet.seek(0)

    # Read PDFs
    new_pdf = PdfReader(packet)
    existing_pdf = PdfReader(input_pdf)
    output = PdfWriter()

    # Merge signature into the selected page
    page = existing_pdf.pages[page_num]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)

    # Add remaining pages
    for i in range(1, len(existing_pdf.pages)):
        output.add_page(existing_pdf.pages[i])

    # Save to file
    with open(output_pdf, "wb") as out_file:
        output.write(out_file)

    return output_pdf


# ----------------- Streamlit UI -----------------
st.title("🖊️ PDF E-Signature Tool")

uploaded_pdf = st.file_uploader("Upload your PDF", type="pdf")

signature_text = st.text_input("Enter your name (signature):")
x = st.number_input("Horizontal position (X)", min_value=0, max_value=800, value=100)
y = st.number_input("Vertical position (Y)", min_value=0, max_value=800, value=100)
page_num = st.number_input("Page number (starting from 0)", min_value=0, value=0)

if uploaded_pdf and signature_text:
    if st.button("Add Signature"):
        output_path = "signed_output.pdf"
        add_signature(uploaded_pdf, output_path, signature_text, x, y, page_num)

        with open(output_path, "rb") as f:
            st.download_button("📥 Download Signed PDF", f, file_name="signed_output.pdf")
