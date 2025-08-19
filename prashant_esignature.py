import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io

st.title("Signature Pad with PDF/Image Upload")

# Step 1: Upload PDF or Image
uploaded_file = st.file_uploader("Upload a PDF or Image", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Convert uploaded bytes into an image
    image = Image.open(io.BytesIO(uploaded_file.read()))
    st.image(image, caption="Uploaded File Preview", use_column_width=True)

    # Step 2: Draw signature on canvas
    st.write("Draw your signature below:")

    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0)",  # Transparent background
        stroke_width=2,
        stroke_color="#000000",
        background_color="#ffffff",
        update_streamlit=True,
        height=150,
        drawing_mode="freedraw",
        key="canvas",
    )

    # Step 3: Show signature
    if canvas_result.image_data is not None:
        st.image(canvas_result.image_data, caption="Your Signature")
