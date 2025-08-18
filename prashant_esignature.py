import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import io

st.set_page_config(page_title="E-Signature App", page_icon="✍️")

st.title("📄 Typed E-Signature Application")
st.write("Upload a PDF/Image, type your name, pick a font, and place your signature.")

# Upload document
uploaded_file = st.file_uploader("Upload a PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

# User input name
user_name = st.text_input("✍️ Enter Your Name for Signature", "John Doe")

# Font options (ensure these .ttf files are available in your working directory)
font_options = {
    "Pacifico": "Pacifico.ttf",
    "Great Vibes": "GreatVibes-Regular.ttf",
    "Dancing Script": "DancingScript-Regular.ttf",
    "Arial": "arial.ttf",
    "Times New Roman": "times.ttf"
}

if uploaded_file and user_name:
    # Load file
    file_type = uploaded_file.type
    if "pdf" in file_type:
        pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        page = pdf[0]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    else:
        img = Image.open(uploaded_file).convert("RGB")

    st.image(img, caption="📄 Uploaded Document", use_container_width=True)

    # Signature preview
    st.subheader("👉 Choose Signature Style")
    selected_style = st.selectbox("Select font style", list(font_options.keys()))

    try:
        font = ImageFont.truetype(font_options[selected_style], 120)  # Larger signature
    except:
        font = ImageFont.load_default()

    # Create transparent signature image
    sig_img = Image.new("RGBA", (1000, 300), (255, 255, 255, 0))
    draw = ImageDraw.Draw(sig_img)
    draw.text((20, 50), user_name, font=font, fill="black")

    st.image(sig_img, caption=f"Signature Preview ({selected_style})")

    # Position controls
    st.subheader("🖼️ Position Signature on Document")
    x_pos = st.slider("Move horizontally (X)", 0, img.width, img.width // 2)
    y_pos = st.slider("Move vertically (Y)", 0, img.height, img.height - 200)

    if st.button("✅ Apply Signature"):
        doc_img = img.copy()
        doc_img.paste(sig_img, (x_pos, y_pos), sig_img)

        st.image(doc_img, caption="✅ Signed Document", use_container_width=True)

        buf = io.BytesIO()
        doc_img.save(buf, format="PNG")
        st.download_button(
            label="⬇️ Download Signed Document",
            data=buf.getvalue(),
            file_name="signed_document.png",
            mime="image/png"
        )
