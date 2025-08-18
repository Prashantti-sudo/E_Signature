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

    st.image(img, caption="📄 Uploaded Document Preview", use_container_width=True)

    st.write("✍️ Choose how you want to sign:")

    sign_method = st.radio(
        "Select Signature Type",
        ["Draw Signature", "Type Signature", "Upload Signature Image"]
    )

    sig = None  # final signature image

    # ------------------- DRAW SIGNATURE -------------------
    if sign_method == "Draw Signature":
        st.write("🖊️ Draw your signature below:")
        canvas_result = st_canvas(
            fill_color="rgba(255,255,255,0)",
            stroke_width=3,
            stroke_color="black",
            background_color="white",
            update_streamlit=True,
            height=180,
            width=500,
            drawing_mode="freedraw",
            key="canvas",
        )
        if canvas_result.image_data is not None:
            sig = Image.fromarray(canvas_result.image_data.astype("uint8")).convert("RGBA")

    # ------------------- TYPE SIGNATURE -------------------
    elif sign_method == "Type Signature":
        user_name = st.text_input("Enter your signature text", "John Doe")
        font_size = st.slider("Font Size", 30, 200, 100)
        font_color = st.color_picker("Font Color", "#000000")

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Dynamic image size to fit text
        dummy_img = Image.new("RGBA", (10, 10), (255, 255, 255, 0))
        draw = ImageDraw.Draw(dummy_img)
        text_width, text_height = draw.textsize(user_name, font=font)

        sig = Image.new("RGBA", (text_width + 40, text_height + 40), (255, 255, 255, 0))
        draw = ImageDraw.Draw(sig)
        draw.text((20, 20), user_name, font=font, fill=font_color)

        st.image(sig, caption="🖊️ Signature Preview")

    # ------------------- UPLOAD SIGNATURE IMAGE -------------------
    else:
        uploaded_sig = st.file_uploader("Upload your signature image", type=["png", "jpg", "jpeg"])
        if uploaded_sig:
            sig = Image.open(uploaded_sig).convert("RGBA")
            st.image(sig, caption="🖋️ Signature Preview")

    # ------------------- APPLY SIGNATURE -------------------
    if sig is not None and st.button("✅ Apply Signature"):
        sig = sig.resize((300, 120), Image.LANCZOS)

        doc_img = img.copy()
        doc_img.paste(sig, (doc_img.width - 350, doc_img.height - 180), sig)

        st.image(doc_img, caption="📄 Signed Document", use_container_width=True)

        buf = io.BytesIO()
        doc_img.save(buf, format="PNG")
        st.download_button(
            label="⬇️ Download Signed Document",
            data=buf.getvalue(),
            file_name="signed_document.png",
            mime="image/png"
        )

