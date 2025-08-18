import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image

st.title("E-Signature App")

# Create a canvas
canvas_result = st_canvas(
    fill_color="rgba(255, 255, 255, 0)",  # Transparent background
    stroke_width=2,
    stroke_color="black",
    background_color="white",
    height=200,
    width=500,
    drawing_mode="freedraw",
    key="canvas"
)

if st.button("Save Signature"):
    if canvas_result.image_data is not None:
        img = Image.fromarray(canvas_result.image_data.astype("uint8"))
        img.save("signature.png")
        st.success("✅ Signature saved as signature.png")
