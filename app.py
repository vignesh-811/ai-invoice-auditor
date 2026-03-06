import pandas as pd
import re
import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes

if "invoice_db" not in st.session_state:
    st.session_state.invoice_db = []

def fraud_detection(invoice_number, total):

    warnings = []

    for inv in st.session_state.invoice_db:
        if inv["invoice_number"] == invoice_number:
            warnings.append("⚠ Duplicate Invoice Detected")

    try:
        amount = float(total.replace(",", ""))
        if amount > 1000000:
            warnings.append("⚠ High Value Invoice – Manual Review Required")
    except:
        pass

    return warnings
# Tell Python where Tesseract is installed

# App title
st.title("AI Invoice Auditor")

st.write("Upload an invoice (PDF or Image) and the AI will extract the text.")

# File uploader
uploaded_file = st.file_uploader(
    "Upload Invoice",
    type=["png", "jpg", "jpeg", "pdf"]
)

if uploaded_file is not None:

    # Convert PDF to image
    if uploaded_file.type == "application/pdf":
        images = convert_from_bytes(uploaded_file.read())
        image = images[0]
    else:
        image = Image.open(uploaded_file)

    # Show invoice preview
    st.subheader("Invoice Preview")
    st.image(image, use_container_width=True)

    # OCR text extraction
    st.subheader("Extracting Text...")
    text = pytesseract.image_to_string(image)

    # Display extracted text
    st.subheader("Extracted Invoice Text")
    st.text_area("Invoice Data", text, height=300)

    # Basic audit checks
    st.subheader("Basic Invoice Checks")

    if "GST" in text or "gst" in text:
        st.success("GST detected in invoice")
    else:
        st.warning("GST not detected")

    if "Total" in text or "TOTAL" in text:
        st.success("Total amount detected")
    else:
        st.warning("Total amount not clearly detected")


    st.info("Invoice processing completed.")

