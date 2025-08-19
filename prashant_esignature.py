import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import io
from streamlit_drawable_canvas import st_canvas

st.title("Drag & Drop E-Signature on PDF")

# Upload PDF
uploaded_pdf = st.file_uploader("Upload your PDF", type=["pdf"])
signature_text = st.text_input("Enter your signature name:")

font_size = st.slider("Font size", 20, 100, 40)
color = st.color_picker("Signature color", "#FF0000")
font_path = "arial.ttf"  # Use any TTF font you have

if uploaded_pdf and signature_text:
    # Generate signature image
    font = ImageFont.truetype(font_path, font_size)
    text_width, text_height = font.getsize(signature_text)
    signature_img = Image.new("RGBA", (text_width + 20, text_height + 20), (255, 255, 255, 0))
    draw = ImageDraw.Draw(signature_img)
    draw.text((10, 10), signature_text, font=font, fill=color)

    st.image(signature_img, caption="Signature Preview")

    # Convert PDF first page to image for canvas
    pdf_bytes = uploaded_pdf.read()
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = pdf_doc[0]
    pix = page.get_pixmap()
    pdf_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    st.markdown("**Drag the signature onto the PDF preview:**")

    canvas_result = st_canvas(
        fill_color="rgba(0,0,0,0)",
        stroke_width=0,
        background_image=pdf_image,
        update_streamlit=True,
        height=pix.height,
        width=pix.width,
        drawing_mode="image",
        image_data=signature_img
    )

    if st.button("Save Signed PDF"):
        if canvas_result.json_data is not None:
            # Get the position of signature
            for obj in canvas_result.json_data["objects"]:
                if obj["type"] == "image":
                    x, y = obj["left"], obj["top"]
                    # Insert signature into PDF
                    sig_byte_arr = io.BytesIO()
                    signature_img.save(sig_byte_arr, format="PNG")
                    sig_byte_arr = sig_byte_arr.getvalue()
                    page.insert_image(fitz.Rect(x, y, x + text_width, y + text_height), stream=sig_byte_arr)

            output_pdf = "signed_pdf.pdf"
            pdf_doc.save(output_pdf)
            pdf_doc.close()
            st.success("PDF signed successfully!")
            st.download_button("Download Signed PDF", data=open(output_pdf, "rb").read(), file_name="signed_pdf.pdf")
