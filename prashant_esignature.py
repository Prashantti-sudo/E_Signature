import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
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

    st.write("✍️ Draw your signature below:")

    # Create canvas for signature
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

    if st.button("Apply Signature"):
        if canvas_result.image_data is not None:
            sig = Image.fromarray(canvas_result.image_data.astype("uint8"))
            sig = sig.convert("RGBA")

            # Resize signature smaller
            sig = sig.resize((150, 60))

            # Place signature at bottom-right of document
            doc_img = img.copy()
            doc_img.paste(sig, (doc_img.width - 200, doc_img.height - 100), sig)

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
