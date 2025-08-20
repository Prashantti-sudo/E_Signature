import streamlit as st
import io
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor

# Try importing pdf2image for preview
try:
    from pdf2image import convert_from_bytes
    PREVIEW_AVAILABLE = True
except ImportError:
    PREVIEW_AVAILABLE = False


def add_signature(input_pdf, signature_text, x, y, page_num, font_size, font_style, font_color):
    # Create a PDF with the signature
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont(font_style, font_size)
    can.setFillColor(HexColor(font_color))   # Apply font color
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
    for i in range(len(existing_pdf.pages)):
        if i != page_num:
            output.add_page(existing_pdf.pages[i])

    # Save to buffer
    output_buffer = io.BytesIO()
    output.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer


# ----------------- Streamlit UI -----------------
st.title("🖊️ PDF E-Signature Tool")

uploaded_pdf = st.file_uploader("Upload your PDF", type="pdf")

signature_text = st.text_input("Enter your name (signature):")

x = st.number_input("Horizontal position (X)", min_value=0, max_value=800, value=100)
y = st.number_input("Vertical position (Y)", min_value=0, max_value=800, value=100)
page_num = st.number_input("Page number (starting from 0)", min_value=0, value=0)

font_size = st.slider("Font Size", min_value=10, max_value=50, value=18)
font_style = st.selectbox("Font Style", ["Helvetica", "Courier", "Times-Roman"])
font_color = st.color_picker("Pick Font Color", "#000000")

if uploaded_pdf and signature_text:
    if st.button("Preview / Sign PDF"):
        signed_pdf = add_signature(
            uploaded_pdf, signature_text, x, y, page_num,
            font_size, font_style, font_color
        )

        # Show preview only if Poppler is available
        if PREVIEW_AVAILABLE:
            try:
                images = convert_from_bytes(
                    signed_pdf.getvalue(),
                    first_page=page_num+1,
                    last_page=page_num+1
                )
                st.image(images[0], caption="Preview of signed PDF", use_container_width=True)
            except Exception as e:
                st.warning("⚠️ Could not generate preview (Poppler missing). You can still download the signed PDF.")
        else:
            st.info("ℹ️ Preview not available (Poppler not installed).")

        # Download button
        st.download_button(
            "📥 Download Signed PDF",
            signed)
