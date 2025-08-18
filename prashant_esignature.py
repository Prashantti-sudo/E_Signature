import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import io

st.set_page_config(page_title="E-Signature on Documents", page_icon="✍️")

st.title("📄 E-Signature Application")
st.write("Upload a file and sign it digitally.")

# Upload file
uploaded_file = st.file_uploader("Upload a PDF or Image", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    file_type = uploaded_file.type
    
    if "pdf" in file_type:
        # Load first page of PDF as preview
        pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        page = pdf[0]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    else:
        # Load image file
        img = Image.open(uploaded_file).convert("RGB")

    st.image(img, caption="Uploaded Document Preview", use_container_width=True)

    st.write("✍️ Choose how you want to sign:")

    # ✅ Fixed line here
    sign_method = st.radio("Select Signature Type", ["Draw Signature", "Type Signature"])

    sig = None  # will hold final signature image

    if sign_method == "Draw Signature":
        st.write("Draw your signature below:")
        canvas_result = st_canvas(
            fill_color="rgba(255,255,255,0)",
            stroke_width=2,
            stroke_color="black",
            background_color="white",
            update_streamlit=True,
            height=150,
            width=400,
            drawing_mode="freedraw",
            key="canvas",
        )

        if canvas_result.image_data is not None:
            sig = Image.fromarray(canvas_result.image_data.astype("uint8")).convert("RGBA")

    else:  # Typed signature
        user_name = st.text_input("Enter your signature text", "John Doe")
        font_size = st.slider("Font Size", 30, 150, 80)
        font_color = st.color_picker("Font Color", "#000000")

        # Try Arial font, fallback if not available
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Create a blank image for text signature
        sig = Image.new("RGBA", (800, 200), (255, 255, 255, 0))
        draw = ImageDraw.Draw(sig)
        draw.text((20, 50), user_name, font=font, fill=font_color)

        st.image(sig, caption="🖊️ Signature Preview")

    if sig is not None and st.button("✅ Apply Signature"):
        # Resize signature smaller for placement
        sig = sig.resize((250, 100), Image.LANCZOS)

        # Place signature at bottom-right of document
        doc_img = img.copy()
        doc_img.paste(sig, (doc_img.width - 300, doc_img.height - 150), sig)

        st.image(doc_img, caption="Signed Document", use_container_width=True)

        # Save as output
        buf = io.BytesIO()
        doc_img.save(buf, format="PNG")
        st.download_button(
            label="⬇️ Download Signed Document",
            data=buf.getvalue(),
            file_name="signed_document.png",
            mime="image/png"
        )
