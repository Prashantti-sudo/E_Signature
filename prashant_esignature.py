=import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import io
from streamlit_drawable_canvas import st_canvas
import numpy as np


# --- Function to render signature text as an image ---
def _render_text_image(text, font, color, opacity):
    dummy_img = Image.new("RGBA", (1000, 1000), (0, 0, 0, 0))
    draw_dummy = ImageDraw.Draw(dummy_img)

    widths, heights = [], []
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


# --- Streamlit App ---
def main():
    st.title("📄 E-Signature PDF App (Drag & Drop)")

    uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"])
    signature_text = st.text_input("Enter your signature text", "Prashant Tiwari")

    if uploaded_pdf and signature_text:
        # Open PDF with PyMuPDF
        pdf_doc = fitz.open(stream=uploaded_pdf.getvalue(), filetype="pdf")
        page = pdf_doc[0]

        # Render first page as preview image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
        pdf_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Show signature preview
        font_size = st.slider("Font size", 20, 100, 50)
        font = ImageFont.truetype("DejaVuSans.ttf", font_size)  # default system font
        sig_img = _render_text_image(signature_text, font, (0, 0, 0, 255), 1.0)

        st.subheader("🖱️ Drag & Drop your signature on the PDF")

        # Convert PIL image to numpy for canvas background
        pdf_image_array = np.array(pdf_image)

        # Drawable canvas for drag & drop
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",
            stroke_width=0,
            background_image=pdf_image_array,
            update_streamlit=True,
            height=pdf_image.height,
            width=pdf_image.width,
            drawing_mode="transform",
            key="canvas",
        )

        # Apply signature button
        if st.button("Apply Signature to PDF"):
            if canvas_result.json_data and "objects" in canvas_result.json_data:
                # Take drag-drop position
                obj = canvas_result.json_data["objects"][-1]
                x, y, w, h = obj["left"], obj["top"], obj["width"], obj["height"]

                # Convert signature image to PNG byte stream
                sig_bytes = io.BytesIO()
                sig_img.save(sig_bytes, format="PNG")
                sig_bytes.seek(0)

                # Insert signature into PDF
                page.insert_image(
                    fitz.Rect(x, y, x + w, y + h),
                    stream=sig_bytes,
                    keep_proportion=True,
                )

                # Save signed PDF
                output_pdf = io.BytesIO()
                pdf_doc.save(output_pdf)
                pdf_doc.close()

                st.success("✅ Signature applied successfully!")
                st.download_button(
                    "Download Signed PDF",
                    data=output_pdf.getvalue(),
                    file_name="signed_document.pdf",
                    mime="application/pdf",
                )


if __name__ == "__main__":
    main()
