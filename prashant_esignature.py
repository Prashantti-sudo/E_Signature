import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import io

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
    st.title("📄 E-Signature PDF App")

    uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"])
    signature_text = st.text_input("Enter your signature text", "Prashant Tiwari")

    if uploaded_pdf and signature_text:
        # Open PDF with PyMuPDF
        pdf_doc = fitz.open(stream=uploaded_pdf.getvalue(), filetype="pdf")
        page = pdf_doc[0]

        # Render first page as preview image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
        pdf_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        st.image(pdf_image, caption="PDF First Page Preview", use_column_width=True)

        # Select font style
        font_size = st.slider("Font size", 20, 100, 50)
        font = ImageFont.truetype("DejaVuSans.ttf", font_size)  # default system font

        # Render signature text as image
        sig_img = _render_text_image(signature_text, font, (0, 0, 0, 255), 1.0)
        st.image(sig_img, caption="Your Signature Preview")

        # Drag & drop positioning (simplified with sliders)
        x = st.slider("X Position", 0, pdf_image.width, 100)
        y = st.slider("Y Position", 0, pdf_image.height, 100)

        if st.button("Apply Signature to PDF"):
            page.insert_image(
                fitz.Rect(x, y, x + sig_img.width, y + sig_img.height),
                stream=io.BytesIO(sig_img.tobytes("png")),
                keep_proportion=True,
            )

            # Save signed PDF
            output_pdf = io.BytesIO()
            pdf_doc.save(output_pdf)
            pdf_doc.close()

            st.success("✅ Signature applied successfully!")
            st.download_button("Download Signed PDF", data=output_pdf.getvalue(),
                               file_name="signed_document.pdf",
                               mime="application/pdf")


if __name__ == "__main__":
    main()
