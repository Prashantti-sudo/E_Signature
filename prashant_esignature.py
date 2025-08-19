import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# ---------------- FONT CONFIG ----------------
FONTS = {
    "Helvetica": None,
    "Helvetica-Bold": None,
    "Times-Roman": None,
    "Times-Bold": None,
    "Courier": None,
    "Courier-Bold": None,
    # Custom fonts if .ttf placed in "fonts/"
    "Alex Brush": "fonts/AlexBrush-Regular.ttf",
    "Dancing Script": "fonts/DancingScript-Regular.ttf",
    "Birthstone": "fonts/Birthstone-Regular.ttf"
}
for font_name, font_path in FONTS.items():
    if font_path and os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont(font_name, font_path))


# ---------------- FUNCTIONS ----------------
def create_signature_text(signature_text, width, height, font_name, font_size):
    """Creates a text signature with underline"""
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    can.setFont(font_name, font_size)
    text_x, text_y = width - 50, 30
    can.drawRightString(text_x, text_y, signature_text)
    text_width = can.stringWidth(signature_text, font_name, font_size)
    can.line(text_x - text_width, text_y - 2, text_x, text_y - 2)
    can.save()
    packet.seek(0)
    return PdfReader(packet)


def create_signature_image(img_path, width, height, scale=0.3):
    """Places uploaded/drawn image at bottom-right"""
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    sig = Image.open(img_path)
    img_width, img_height = sig.size
    new_width = width * scale
    new_height = (img_height / img_width) * new_width
    can.drawImage(img_path, width - new_width - 30, 20, new_width, new_height, mask="auto")
    can.save()
    packet.seek(0)
    return PdfReader(packet)


def add_signature_to_pdf(uploaded_file, mode, text=None, font_name=None, font_size=14, img_path=None):
    reader = PdfReader(uploaded_file)
    writer = PdfWriter()

    for page in reader.pages:
        width, height = float(page.mediabox.width), float(page.mediabox.height)

        if mode == "Text":
            sig_pdf = create_signature_text(text, width, height, font_name, font_size)
        elif mode == "Upload Image":
            sig_pdf = create_signature_image(img_path, width, height, scale=0.25)
        elif mode == "Draw":
            sig_pdf = create_signature_image(img_path, width, height, scale=0.25)

        page.merge_page(sig_pdf.pages[0])
        writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output


# ---------------- STREAMLIT UI ----------------
st.title("✍️ PDF E-Signature App")

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])
mode = st.radio("Choose Signature Method", ["Text", "Upload Image", "Draw"])

signature_text = None
font_name, font_size = "Helvetica-Bold", 18
signature_img_path = None

if mode == "Text":
    signature_text = st.text_input("Enter Signature Text (Name)", "")
    available_fonts = [f for f in FONTS.keys() if (FONTS[f] is None or os.path.exists(FONTS[f]))]
    font_name = st.selectbox("Choose Font Style", available_fonts)
    font_size = st.slider("Font Size", 10, 48, 18)

elif mode == "Upload Image":
    uploaded_sig = st.file_uploader("Upload Signature Image (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if uploaded_sig:
        signature_img_path = "uploaded_signature.png"
        with open(signature_img_path, "wb") as f:
            f.write(uploaded_sig.read())
        st.image(signature_img_path, caption="Uploaded Signature Preview", use_container_width=False)

elif mode == "Draw":
    st.write("Draw your signature below 👇")
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=2,
        stroke_color="black",
        background_color="white",
        height=150,
        width=400,
        drawing_mode="freedraw",
        key="canvas",
    )
    if canvas_result.image_data is not None:
        img = Image.fromarray((canvas_result.image_data).astype("uint8"))
        signature_img_path = "drawn_signature.png"
        img.save(signature_img_path)

if uploaded_file:
    if st.button("Add Signature to PDF"):
        if mode == "Text" and signature_text.strip() == "":
            st.error("Please enter your signature text!")
        elif mode in ["Upload Image", "Draw"] and not signature_img_path:
            st.error("Please provide/upload a signature image!")
        else:
            signed_pdf = add_signature_to_pdf(
                uploaded_file,
                mode,
                text=signature_text,
                font_name=font_name,
                font_size=font_size,
                img_path=signature_img_path,
            )
            st.success("✅ Signature added to PDF successfully!")
            st.download_button(
                "📥 Download Signed PDF",
                data=signed_pdf,
                file_name="signed_document.pdf",
                mime="application/pdf"
            )
