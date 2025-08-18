import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import io

st.set_page_config(page_title="E-Signature on PDF", page_icon="✍️")

st.title("📄 E-Signature on PDF")
st.write("Upload a PDF, type your name, and place your signature.")

# Step 1: Upload PDF
uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

# Step 2: Enter Name
user_name = st.text_input("✍️ Enter Your Name", "John Doe")

# Step 3: Font options
font_options = {
    "Arial": "arial.ttf",
    "Times New Roman": "times.ttf",
    "Pacifico": "Pacifico.ttf",   # make sure fonts exist in your project
    "Great Vibes": "GreatVibes-Regular.ttf",
    "Dancing Script": "DancingScript-Regular.ttf"
}

if uploaded_file and user_name:
    # Load PDF first page
    pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    page = pdf[0]
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    st.image(img, caption="📄 PDF Preview (First Page)", use_container_width=True)

    # Select font and size
    selected_style = st.selectbox("Select Font Style", list(font_options.keys()))
    font_size = st.slider("Font Size", 40, 200, 100)

    try:
        font = ImageFont.truetype(font_options[selected_style], font_size)
    except:
        font = ImageFont.load_default()

    # Create signature preview
    sig_img = Image.new("RGBA", (1000, 300), (255, 255, 255, 0))
    draw = ImageDraw.Draw(sig_img)
    draw.text((20, 50), user_name, font=font, fill="black")

    st.image(sig_img, caption=f"🖊️ Signature Preview ({selected_style})")

    # Position with sliders (basic way)
    st.subheader("📍 Place Signature")
    x_pos = st.slider("Move horizontally (X)", 0, img.width, img.width // 2)
    y_pos = st.slider("Move vertically (Y)", 0, img.height, img.height // 2)

    if st.button("✅ Apply Signature to PDF"):
        doc_img = img.copy()
        doc_img.paste(sig_img, (x_pos, y_pos), sig_img)

        # Show final signed image
        st.image(doc_img, caption="✅ Signed Document")

        # Save as PDF
        output_pdf = fitz.open()
        rect = fitz.Rect(0, 0, doc_img.width, doc_img.height)
        pdfbytes = io.BytesIO()
        doc_img.save(pdfbytes, format="PNG")
        img_pdf = output_pdf.new_page(width=rect.width, height=rect.height)
        img_pdf.insert_image(rect, stream=pdfbytes.getvalue())
        buf = io.BytesIO()
        output_pdf.save(buf)

        st.download_button(
            label="⬇️ Download Signed PDF",
            data=buf.getvalue(),
            file_name="signed_document.pdf",
            mime="application/pdf"
        )
