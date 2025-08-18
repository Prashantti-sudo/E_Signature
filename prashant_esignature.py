import io
import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from streamlit_drawable_canvas import st_canvas
from pdf2image import convert_from_bytes

st.set_page_config(page_title="PDF E-Signature", layout="wide")
st.title("✍️ Interactive PDF E-Signature Tool")

uploaded_pdf = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_pdf:
    reader = PdfReader(uploaded_pdf)

    # Convert first page to image for preview
    images = convert_from_bytes(uploaded_pdf.read(), first_page=1, last_page=1)
    preview_img = images[0]

    # Resize preview for UI
    w, h = preview_img.size
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=0,
        background_image=preview_img,
        update_streamlit=True,
        height=h,
        width=w,
        drawing_mode="point",
        key="canvas",
    )

    # Signature input
    signature_text = st.text_input("Enter your signature", "John Doe")
    font_size = st.slider("Font size", 8, 48, 18)

    if st.button("Apply Signature") and canvas_result.json_data is not None:
        # Get user click position
        if len(canvas_result.json_data["objects"]) > 0:
            obj = canvas_result.json_data["objects"][-1]  # last click
            x, y = obj["left"], obj["top"]

            writer = PdfWriter()
            for page in reader.pages:
                packet = io.BytesIO()
                c = canvas.Canvas(packet, pagesize=(float(page.mediabox.width),
                                                    float(page.mediabox.height)))
                c.setFont("Helvetica-Bold", font_size)
                c.setFillColor(HexColor("#000000"))
                c.drawString(x, float(page.mediabox.height) - y, signature_text)
                c.save()

                packet.seek(0)
                overlay = PdfReader(packet)
                page.merge_page(overlay.pages[0])
                writer.add_page(page)

            output = io.BytesIO()
            writer.write(output)
            output.seek(0)

            st.success("✅ Signature applied successfully!")
            st.download_button(
                label="📥 Download Signed PDF",
                data=output,
                file_name="signed_document.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("⚠️ Please click on the PDF preview to place your signature.")
