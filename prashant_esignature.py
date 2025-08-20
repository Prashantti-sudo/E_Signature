import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont
import io

st.set_page_config(page_title="E-Signature App", layout="wide")
st.title("✍️ E-Signature on PDF")

# Step 1: Upload PDF
uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])

# Step 2: Write your name
name_input = st.text_input("Enter your Name (this will be your signature):")

# Generate a signature image from text
signature_img = None
if name_input:
    font = ImageFont.load_default()  # use system default font
    img = Image.new("RGBA", (400, 100), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.text((10, 30), name_input, font=font, fill=(0, 0, 0))
    signature_img = img
    st.image(signature_img, caption="Generated Signature")

# Step 3: Drag & drop signature placement
if uploaded_pdf and signature_img:
    st.subheader("📍 Place your Signature")
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=0,
        background_color="#f0f0f0",
        update_streamlit=True,
        width=500,
        height=300,
        drawing_mode="transform",
        key="canvas",
    )

    if st.button("Save Signed PDF"):
        # Read PDF
        pdf_reader = PdfReader(uploaded_pdf)
        pdf_writer = PdfWriter()
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)

        # Convert signature to image object
        sig_io = io.BytesIO()
        signature_img.save(sig_io, format="PNG")
        sig_io.seek(0)
        sig_reader = ImageReader(sig_io)

        # Create overlay with signature
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        # Example: place at bottom-right (fixed)
        can.drawImage(sig_reader, 200, 100, width=150, height=50, mask="auto")
        can.save()

        # Merge overlay with PDF
        packet.seek(0)
        new_pdf = PdfReader(packet)
        page = pdf_writer.pages[0]
        page.merge_page(new_pdf.pages[0])

        output = io.BytesIO()
        pdf_writer.write(output)
        output.seek(0)

        st.download_button("📥 Download Signed PDF", output, "signed_document.pdf", "application/pdf")
