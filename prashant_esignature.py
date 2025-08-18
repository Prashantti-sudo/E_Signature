import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os

# Register custom fonts (make sure these .ttf files exist in "fonts" folder)
FONTS = {
    "Helvetica": None,
    "Helvetica-Bold": None,
    "Times-Roman": None,
    "Times-Bold": None,
    "Courier": None,
    "Courier-Bold": None,
    "Alex Brush": "fonts/AlexBrush-Regular.ttf",
    "Dancing Script": "fonts/DancingScript-Regular.ttf",
    "Birthstone": "fonts/Birthstone-Regular.ttf"
}

for font_name, font_path in FONTS.items():
    if font_path and os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont(font_name, font_path))

def create_signature_pdf(signature_text, width, height, font_name="Helvetica-Bold", font_size=14, margin_x=50, margin_y=30):
    """
    Creates a temporary PDF with signature text + underline at bottom-right
    """
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    can.setFont(font_name, font_size)

    # Draw signature
    text_x = width - margin_x
    text_y = margin_y
    can.drawRightString(text_x, text_y, signature_text)

    # Draw underline
    text_width = can.stringWidth(signature_text, font_name, font_size)
    underline_y = text_y - 2
    can.line(text_x - text_width, underline_y, text_x, underline_y)

    can.save()
    packet.seek(0)
    return PdfReader(packet)

def add_signature_to_pdf(uploaded_file, signature_text, font_name, font_size):
    reader = PdfReader(uploaded_file)
    writer = PdfWriter()

    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        # Create signature layer
        sig_pdf = create_signature_pdf(signature_text, width, height, font_name, font_size)
        sig_page = sig_pdf.pages[0]

        # Merge signature on page
        page.merge_page(sig_page)
        writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output


# ---------------- STREAMLIT UI ----------------
st.title("✍️ PDF E-Signature App")

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])
signature_text = st.text_input("Enter your Signature Text (Name)", "")

# Font style dropdown (includes custom fonts if available)
available_fonts = [f for f in FONTS.keys() if (FONTS[f] is None or os.path.exists(FONTS[f]))]
font_name = st.selectbox("Choose Signature Font Style", available_fonts)

# Font size slider
font_size = st.slider("Select Font Size", 10, 48, 18)

if uploaded_file and signature_text:
    if st.button("Add Signature"):
        signed_pdf = add_signature_to_pdf(uploaded_file, signature_text, font_name, font_size)

        st.success(f"✅ Signature added with {font_name} style at bottom-right corner!")
        st.download_button(
            label="📥 Download Signed PDF",
            data=signed_pdf,
            file_name="signed_document.pdf",
            mime="application/pdf"
        )
