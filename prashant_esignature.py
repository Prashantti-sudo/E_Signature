import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pdf2image import convert_from_bytes
import tempfile

st.set_page_config(page_title="E-Signature App", layout="wide")

st.title("📑 E-Signature App")

st.markdown("""
⚠️ **Note**: True drag-and-drop needs a custom front-end.  
This app **mimics** the effect: you draw a box on the page,  
and your signature text will be placed there.
""")

# Step 1: Upload PDF
uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

# Step 2: Enter signature text
signature_text = st.text_input("Enter your signature text:")
font_size = st.slider("Font Size", 20, 80, 40)

if uploaded_file and signature_text:
    # Read PDF
    pdf_bytes = uploaded_file.read()
    pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(pdf_reader.pages)
    st.write(f"📄 Total Pages: {total_pages}")

    # Select page to sign
    page_number = st.number_input("Select page number", 1, total_pages, 1)

    # Step 3: Convert selected PDF page to image for preview
    images = convert_from_bytes(pdf_bytes, dpi=150)
    page_img = images[page_number - 1]

    # Step 4: Show page in canvas background
    st.write("👉 Draw a red box where you want to place the signature:")
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.0)",
        stroke_width=2,
        stroke_color="red",
        background_image=page_img,
        update_streamlit=True,
        height=page_img.height,
        width=page_img.width,
        drawing_mode="rect",
        key="canvas",
    )

    # Step 5: Place signature in PDF
    if st.button("✅ Place Signature and Save PDF"):
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]

            if len(objects) > 0:
                # Create temp PDF with signature(s)
                temp_sig = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                c = canvas.Canvas(temp_sig.name, pagesize=letter)
                c.setFont("Helvetica", font_size)

                page_height = letter[1]  # Letter page height (792 pts)
                for obj in objects:
                    x, y = obj["left"], obj["top"]
                    c.drawString(x, page_height - y, signature_text)  # invert Y
                c.save()

                # Merge into original PDF
                pdf_writer = PdfWriter()
                for i, page in enumerate(pdf_reader.pages):
                    if i == page_number - 1:
                        sig_reader = PdfReader(temp_sig.name)
                        page.merge_page(sig_reader.pages[0])
                    pdf_writer.add_page(page)

                output_filename = "signed_output.pdf"
                with open(output_filename, "wb") as out:
                    pdf_writer.write(out)

                st.success("✅ Signature placed successfully!")
                with open(output_filename, "rb") as f:
                    st.download_button("⬇️ Download Signed PDF", f, file_name="signed_output.pdf")
            else:
                st.warning("⚠️ Please draw a box on the page to place the signature.")
