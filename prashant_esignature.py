import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import fitz  # PyMuPDF
import os, requests

# 🎨 Fonts from Google
FONTS = {
    "Dancing Script": "https://github.com/google/fonts/raw/main/ofl/dancingscript/DancingScript-Regular.ttf",
    "Alex Brush": "https://github.com/google/fonts/raw/main/ofl/alexbrush/AlexBrush-Regular.ttf",
    "Birthstone": "https://github.com/google/fonts/raw/main/ofl/birthstone/Birthstone-Regular.ttf",
}

os.makedirs("fonts", exist_ok=True)

def load_font(font_name):
    url = FONTS.get(font_name)
    path = f"fonts/{font_name.replace(' ', '')}.ttf"
    if url and not os.path.exists(path):
        r = requests.get(url)
        with open(path, "wb") as f:
            f.write(r.content)
    try:
        pdfmetrics.registerFont(TTFont(font_name, path))
        return font_name
    except:
        return "Helvetica"

def pdf_page_to_image(pdf_bytes):
    """Render first PDF page as image for drag-drop canvas"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    pix = page.get_pixmap()
    return pix.tobytes("png")

def add_signature(input_pdf, signature_text, font_name, x, y):
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)
    c.setFont(font_name, 36)
    c.drawString(x, y, signature_text)
    c.save()
    packet.seek(0)

    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    sig_pdf = PdfReader(packet)
    sig_page = sig_pdf.pages[0]

    for i, page in enumerate(reader.pages):
        if i == 0:  # only first page
            page.merge_page(sig_page)
        writer.add_page(page)

    output_stream = BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    return output_stream


# ================== Streamlit UI ==================
st.title("🖊️ Drag & Drop E-Signature")

uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])
signature_text = st.text_input("Enter your signature text")
font_choice = st.selectbox("Choose font", list(FONTS.keys()))
font_name = load_font(font_choice)

if uploaded_pdf and signature_text:
    pdf_bytes = uploaded_pdf.read()
    img_bytes = pdf_page_to_image(pdf_bytes)

    st.markdown("### Drag your signature on the PDF preview")

    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.0)",  # transparent
        stroke_width=0,
        background_image=img_bytes,
        update_streamlit=True,
        height=600,
        width=450,
        drawing_mode="transform",  # allows drag/drop box
        key="canvas",
    )

    if st.button("Apply Signature"):
        if canvas_result.json and len(canvas_result.json["objects"]) > 0:
            obj = canvas_result.json["objects"][0]
            x = obj["left"]
            y = 600 - obj["top"]  # flip y-axis
            signed_pdf = add_signature(BytesIO(pdf_bytes), signature_text, font_name, x, y)
            st.download_button("📥 Download Signed PDF", data=signed_pdf,
                               file_name="signed_output.pdf", mime="application/pdf")
        else:
            st.warning("⚠️ Please place your signature on the page.")
