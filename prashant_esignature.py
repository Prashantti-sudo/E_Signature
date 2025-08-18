import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

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
st.title("📄 PDF E-Signature App")

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])
signature_text = st.text_input("Enter your Signature Text (Name)", "")

# Font style dropdown
font_name = st.selectbox(
    "Choose Signature Font Style",
    ["Helvetica", "Helvetica-Bold", "Times-Roman", "Times-Bold", "Courier", "Courier-Bold"]
)

# Font size slider
font_size = st.slider("Select Font Size", 10, 36, 14)

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
