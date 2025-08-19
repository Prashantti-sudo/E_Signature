import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os, requests

# 🎨 Fonts from Google
FONTS = {
    "Dancing Script": "https://github.com/google/fonts/raw/main/ofl/dancingscript/DancingScript-Regular.ttf",
    "Alex Brush": "https://github.com/google/fonts/raw/main/ofl/alexbrush/AlexBrush-Regular.ttf",
    "Birthstone": "https://github.com/google/fonts/raw/main/ofl/birthstone/Birthstone-Regular.ttf",
}

os.makedirs("fonts", exist_ok=True)

def load_font(font_name):
    """Download font if missing & register it"""
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
        return "Helvetica"  # fallback

def add_signature(input_pdf, signature_text, font_name, x, y):
    """Overlay signature text on PDF"""
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)
    c.setFont(font_name, 36)
    c.drawString(x, y, signature_text)
    c.save()   # ✅ FIXED: properly closed
    packet.seek(0)

    # Merge with original PDF
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    sig_pdf = PdfReader(packet)
    sig_page = sig_pdf.pages[0]

    for i, page in enumerate(reader.pages):
        if i == 0:  # Only first page for demo
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

st.markdown("### Drag and Drop Signature Placement")
st.write("👉 Use sliders to move your signature around the page.")

# Simulated drag & drop with sliders
x = st.slider("Move horizontally", 50, 500, 200)
y = st.slider("Move vertically", 50, 700, 100)

if uploaded_pdf and signature_text:
    if st.button("Apply Signature"):
        signed_pdf = add_signature(uploaded_pdf, signature_text, font_name, x, y)
        st.download_button("📥 Download Signed PDF", data=signed_pdf,
                           file_name="signed_output.pdf", mime="application/pdf")
