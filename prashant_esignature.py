import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes
import io
from streamlit_drawable_canvas import st_canvas

# -------- FIXED RENDER FUNCTION (works with Pillow >=10) --------
def _render_text_image(text, font, color, opacity):
    dummy_img = Image.new("RGBA", (1000, 1000), (0, 0, 0, 0))
    draw_dummy = ImageDraw.Draw(dummy_img)

    widths = []
    heights = []
    for ch in text:
        bbox = draw_dummy.textbbox((0, 0), ch, font=font)
        ch_w, ch_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        widths.append(ch_w)
        heights.append(ch_h)

    total_width = sum(widths)
    max_height = max(heights)

    img = Image.new("RGBA", (total_width, max_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    x = 0
    for ch, w in zip(text, widths):
        draw.text((x, 0), ch, font=font, fill=color)
        x += w

    # Apply opacity
    alpha = img.split()[3]
    alpha = alpha.point(lambda p: int(p * opacity))
    img.putalpha(alpha)

    return img


# -------- STREAMLIT APP --------
def main():
    st.set_page_config(page_title="E-Signature PDF App", layout="wide")
    st.title("✍️ E-Signature PDF App")

    uploaded_pdf = st.file_uploader("📂 Upload a PDF", type=["pdf"])

    if uploaded_pdf:
        # Convert PDF first page to image for preview
        images = convert_from_bytes(uploaded_pdf.read(), first_page=1, last_page=1)
        pdf_image = images[0]
        st.image(pdf_image, caption="PDF First Page Preview", use_column_width=True)

        # Signature text input
        text = st.text_input("Enter your signature text")
        font_size = st.slider("Font Size", 20, 100, 50)
        opacity = st.slider("Opacity", 0.1, 1.0, 1.0)

        if text:
            font = ImageFont.truetype("fonts/AlexBrush-Regular.ttf", font_size)
            sig_img = _render_text_image(text, font, (0, 0, 0, 255), opacity)

            # Drag & Drop signature
            st.write("⬇️ Drag & drop your signature on the PDF preview")
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 0)",
                stroke_width=0,
                background_image=pdf_image,
                update_streamlit=True,
                height=pdf_image.height,
                width=pdf_image.width,
                drawing_mode="transform",
                key="canvas",
            )

            if canvas_result.image_data is not None:
                st.image(sig_img, caption="Signature Preview")

        # Button to save signature on PDF
        if st.button("✅ Save Signature to PDF"):
            pdf_doc = fitz.open(stream=uploaded_pdf.getvalue(), filetype="pdf")
            page = pdf_doc[0]

            # Example: place signature at fixed coords
            rect = fitz.Rect(100, 700, 300, 750)
            sig_bytes = io.BytesIO()
            sig_img.save(sig_bytes, format="PNG")

            page.insert_image(rect, stream=sig_bytes.getvalue())
            output_pdf = io.BytesIO()
            pdf_doc.save(output_pdf)

            st.download_button(
                "⬇️ Download Signed PDF",
                data=output_pdf,
                file_name="signed_output.pdf",
                mime="application/pdf",
            )


if __name__ == "__main__":
    main()
