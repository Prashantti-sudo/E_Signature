import streamlit as st
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pdf2image import convert_from_bytes
from streamlit_drawable_canvas import st_canvas
from PIL import Image

# Function to add signature at (x, y)
def create_signature_text(signature_text, width, height, font_name, font_size, x, y):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    can.setFont(font_name, font_size)
    can.drawString(x, y, signature_text)
    can.save()
    packet.seek(0)
    return PdfReader(packet)

def add_signature_to_pdf(uploaded_file, text, font_name, font_size, x, y):
    reader = PdfReader(uploaded_file)
    writer = PdfWriter()

    for page in reader.pages:
        width, height = float(page.mediabox.width), float(page.mediabox.height)
        sig_pdf = create_signature_text(text, width, height, font_name, font_size, x, y)
        page.merge_page(sig_pdf.pages[0])
        writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output


st.title("Drag Signature on PDF")

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
if uploaded_file:
    images = convert_from_bytes(uploaded_file.read())
    st.image(images[0], caption="Page 1 Preview", use_column_width=True)

    # Canvas overlay
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",  # Transparent fill
        stroke_width=2,
        stroke_color="red",
        background_image=images[0],
        update_streamlit=True,
        height=600,
        width=500,
        drawing_mode="transform",  # allow dragging
        key="canvas",
    )

    # Get coordinates
    if canvas_result.json_data is not None:
        for obj in canvas_result.json_data["objects"]:
            x, y = obj["left"], obj["top"]
            st.write(f"Signature coordinates: ({x}, {y})")

    # Apply signature
    if st.button("Apply Signature"):
        output = add_signature_to_pdf(uploaded_file, "My Signature", "Helvetica", 16, x, y)
        st.download_button("Download Signed PDF", output, "signed.pdf")
