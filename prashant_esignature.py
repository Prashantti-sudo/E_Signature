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
    c.save(
