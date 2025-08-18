import streamlit as st
from PIL import Image
import io

st.set_page_config(page_title="Upload & Place Signature", page_icon="✍️")

st.title("📄 Digital Signature App")
st.write("Upload a document and your signature, then place it on the document.")

# Upload document
uploaded_doc = st.file_uploader("Upload a Document (Image)", type=["png", "jpg", "jpeg"])
# Upload signature
uploaded_sign = st.file_uploader("Upload Your Signature (PNG preferred)", type=["png", "jpg", "jpeg"])

if uploaded_doc and uploaded_sign:
    # Load images
    doc_img = Image.open(uploaded_doc).convert("RGBA")
    sign_img = Image.open(uploaded_sign).convert("RGBA")

    # Resize signature for easier placement
    sign_img = sign_img.resize((150, 60))

    st.image(doc_img, caption="Uploaded Document", use_container_width=True)

    st.write("👉 Select where to place your signature")

    # Slider for position
    x_pos = st.slider("X Position", 0, doc_img.width, doc_img.width // 2)
    y_pos = st.slider("Y Position", 0, doc_img.height, doc_img.height - 100)

    # Preview signed document
    preview_img = doc_img.copy()
    preview_img.paste(sign_img, (x_pos, y_pos), sign_img)

    st.image(preview_img, caption="Signed Document Preview", use_container_width=True)

    # Download button
    buf = io.BytesIO()
    preview_img.save(buf, format="PNG")
    st.download_button(
        label="⬇️ Download Signed Document",
        data=buf.getvalue(),
        file_name="signed_document.png",
        mime="image/png"
    )
