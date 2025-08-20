import streamlit as st
import io
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
import fitz  # PyMuPDF for preview
import streamlit.components.v1 as components
import base64


def add_signature(input_pdf, signature_text, x, y, page_num, font_size, font_style, font_color):
    # Create a PDF with the signature
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont(font_style, font_size)
    can.setFillColor(HexColor(font_color))   # Apply font color
    can.drawString(x, y, signature_text)
    can.save()

    # Move to start
    packet.seek(0)

    # Read PDFs
    new_pdf = PdfReader(packet)
    existing_pdf = PdfReader(input_pdf)
    output = PdfWriter()

    # Merge signature into the selected page
    page = existing_pdf.pages[page_num]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)

    # Add remaining pages
    for i in range(len(existing_pdf.pages)):
        if i != page_num:
            output.add_page(existing_pdf.pages[i])

    # Save to buffer
    output_buffer = io.BytesIO()
    output.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer


def preview_pdf(pdf_bytes, page_num=0):
    """Render PDF page as image using PyMuPDF (no Poppler needed)."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(page_num)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for clarity
    img_bytes = pix.tobytes("png")
    return img_bytes


def create_draggable_signature_component(pdf_base64, signature_text, font_size, font_color, page_width=612, page_height=792):
    """Create an interactive component for dragging signature on PDF."""
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .pdf-container {{
                position: relative;
                display: inline-block;
                border: 2px solid #ddd;
                border-radius: 8px;
                overflow: hidden;
            }}
            .pdf-image {{
                display: block;
                max-width: 100%;
                height: auto;
            }}
            .signature {{
                position: absolute;
                background: rgba(255, 255, 255, 0.8);
                border: 2px dashed #007bff;
                border-radius: 4px;
                padding: 4px 8px;
                cursor: move;
                font-family: Arial, sans-serif;
                font-size: {font_size}px;
                color: {font_color};
                user-select: none;
                z-index: 10;
                min-width: 100px;
                text-align: center;
            }}
            .signature:hover {{
                background: rgba(255, 255, 255, 0.9);
                border-color: #0056b3;
            }}
            .coordinates {{
                position: absolute;
                top: 10px;
                right: 10px;
                background: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 20;
            }}
        </style>
    </head>
    <body>
        <div class="pdf-container" id="pdfContainer">
            <img src="data:image/png;base64,{pdf_base64}" class="pdf-image" id="pdfImage">
            <div class="signature" id="signature">{signature_text}</div>
            <div class="coordinates" id="coordinates">X: 100, Y: 100</div>
        </div>

        <script>
            let isDragging = false;
            let currentX = 100;
            let currentY = 100;
            let initialX = 0;
            let initialY = 0;
            let xOffset = 0;
            let yOffset = 0;

            const signature = document.getElementById('signature');
            const coordinates = document.getElementById('coordinates');
            const pdfContainer = document.getElementById('pdfContainer');
            const pdfImage = document.getElementById('pdfImage');

            // Set initial position
            signature.style.left = currentX + 'px';
            signature.style.top = currentY + 'px';

            function updateCoordinates() {{
                const containerRect = pdfContainer.getBoundingClientRect();
                const imageRect = pdfImage.getBoundingClientRect();
                
                // Calculate relative position within the image
                const relativeX = Math.max(0, Math.min(currentX, imageRect.width - signature.offsetWidth));
                const relativeY = Math.max(0, Math.min(currentY, imageRect.height - signature.offsetHeight));
                
                // Convert to PDF coordinates (PDF coordinate system has origin at bottom-left)
                const pdfX = Math.round((relativeX / imageRect.width) * {page_width});
                const pdfY = Math.round({page_height} - ((relativeY + signature.offsetHeight) / imageRect.height) * {page_height});
                
                coordinates.textContent = `X: ${{pdfX}}, Y: ${{pdfY}}`;
                
                // Send coordinates to Streamlit
                window.parent.postMessage({{
                    type: 'signature_position',
                    x: pdfX,
                    y: pdfY
                }}, '*');
            }}

            signature.addEventListener('mousedown', dragStart);
            document.addEventListener('mousemove', drag);
            document.addEventListener('mouseup', dragEnd);

            function dragStart(e) {{
                initialX = e.clientX - xOffset;
                initialY = e.clientY - yOffset;

                if (e.target === signature) {{
                    isDragging = true;
                }}
            }}

            function drag(e) {{
                if (isDragging) {{
                    e.preventDefault();
                    
                    currentX = e.clientX - initialX;
                    currentY = e.clientY - initialY;

                    xOffset = currentX;
                    yOffset = currentY;

                    const containerRect = pdfContainer.getBoundingClientRect();
                    
                    // Constrain within container bounds
                    currentX = Math.max(0, Math.min(currentX, containerRect.width - signature.offsetWidth));
                    currentY = Math.max(0, Math.min(currentY, containerRect.height - signature.offsetHeight));

                    signature.style.left = currentX + 'px';
                    signature.style.top = currentY + 'px';
                    
                    updateCoordinates();
                }}
            }}

            function dragEnd(e) {{
                initialX = currentX;
                initialY = currentY;
                isDragging = false;
            }}

            // Initial coordinate update
            updateCoordinates();
        </script>
    </body>
    </html>
    """
    
    return html_code


# ----------------- Streamlit UI -----------------
st.title("🖊️ PDF E-Signature Tool")

uploaded_pdf = st.file_uploader("Upload your PDF", type="pdf")

if uploaded_pdf:
    # Initialize session state for coordinates
    if 'signature_x' not in st.session_state:
        st.session_state.signature_x = 100
    if 'signature_y' not in st.session_state:
        st.session_state.signature_y = 100

    col1, col2 = st.columns([1, 1])
    
    with col1:
        signature_text = st.text_input("Enter your name (signature):", value="Your Signature")
        page_num = st.number_input("Page number (starting from 0)", min_value=0, value=0)
        
    with col2:
        font_size = st.slider("Font Size", min_value=10, max_value=50, value=18)
        font_style = st.selectbox("Font Style", ["Helvetica", "Courier", "Times-Roman"])
        font_color = st.color_picker("Pick Font Color", "#000000")

    if signature_text:
        st.markdown("### 📍 Position Your Signature")
        st.info("👆 Drag the signature box on the PDF preview below to position it where you want!")
        
        # Get PDF info for the selected page
        try:
            pdf_reader = PdfReader(uploaded_pdf)
            if page_num < len(pdf_reader.pages):
                # Create a temporary PDF with just the selected page for preview
                temp_pdf = io.BytesIO()
                temp_writer = PdfWriter()
                temp_writer.add_page(pdf_reader.pages[page_num])
                temp_writer.write(temp_pdf)
                temp_pdf.seek(0)
                
                # Generate preview image
                img_bytes = preview_pdf(temp_pdf.getvalue(), 0)
                pdf_base64 = base64.b64encode(img_bytes).decode()
                
                # Get page dimensions
                page = pdf_reader.pages[page_num]
                page_width = float(page.mediabox.width)
                page_height = float(page.mediabox.height)
                
                # Create draggable component
                draggable_html = create_draggable_signature_component(
                    pdf_base64, signature_text, font_size, font_color, page_width, page_height
                )
                
                # Display the interactive component
                components.html(draggable_html, height=600, scrolling=True)
                
                # Display current coordinates
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("X Position", st.session_state.signature_x)
                with col2:
                    st.metric("Y Position", st.session_state.signature_y)
                with col3:
                    st.metric("Page", page_num + 1)
                
                # Manual coordinate input (optional)
                with st.expander("🎯 Manual Position Adjustment"):
                    manual_x = st.number_input("X Position", min_value=0, max_value=int(page_width), 
                                             value=st.session_state.signature_x, key="manual_x")
                    manual_y = st.number_input("Y Position", min_value=0, max_value=int(page_height), 
                                             value=st.session_state.signature_y, key="manual_y")
                    if st.button("Update Position"):
                        st.session_state.signature_x = manual_x
                        st.session_state.signature_y = manual_y
                        st.rerun()
                
                # Generate signed PDF button
                if st.button("🖊️ Generate Signed PDF", type="primary"):
                    signed_pdf = add_signature(
                        uploaded_pdf, signature_text, 
                        st.session_state.signature_x, st.session_state.signature_y, 
                        page_num, font_size, font_style, font_color
                    )
                    
                    st.success("✅ PDF signed successfully!")
                    
                    # Download button
                    st.download_button(
                        "📥 Download Signed PDF",
                        signed_pdf,
                        file_name=f"signed_{uploaded_pdf.name}",
                        mime="application/pdf",
                        type="primary"
                    )
                    
            else:
                st.error(f"Page {page_num} does not exist. This PDF has {len(pdf_reader.pages)} pages.")
                
        except Exception as e:
            st.error(f"Error processing PDF: {e}")

# JavaScript to handle coordinate updates from the draggable component
st.markdown("""
<script>
window.addEventListener('message', function(event) {
    if (event.data.type === 'signature_position') {
        // Update Streamlit session state (this requires a custom approach)
        console.log('New position:', event.data.x, event.data.y);
    }
});
</script>
""", unsafe_allow_html=True)
