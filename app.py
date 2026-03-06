import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import pandas as pd
import re

# -----------------------------
# PAGE SETTINGS
# -----------------------------

st.set_page_config(
    page_title="SmartAudit AI",
    layout="wide"
)

# -----------------------------
# UI STYLE
# -----------------------------

st.markdown("""
<style>

.stApp {
background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
color:white;
}

h1,h2,h3 {
color:#00ffd5;
}

.block-container {
padding-top:2rem;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# TITLE
# -----------------------------

st.title("🧠 SmartAudit AI")
st.subheader("AI-Powered Invoice Fraud Detection Platform")

st.write(
"""
Upload invoices and let AI automatically extract data,
detect suspicious invoices, and generate risk analytics.
"""
)

# -----------------------------
# DATABASE STORAGE
# -----------------------------

if "invoice_db" not in st.session_state:
    st.session_state.invoice_db = []

# -----------------------------
# DASHBOARD
# -----------------------------

st.subheader("📊 Audit Dashboard")

total_invoices = len(st.session_state.invoice_db)

high_risk = sum(1 for x in st.session_state.invoice_db if x.get("risk",0) > 60)

medium_risk = sum(1 for x in st.session_state.invoice_db if 30 < x.get("risk",0) <= 60)

low_risk = sum(1 for x in st.session_state.invoice_db if x.get("risk",0) <= 30)

col1,col2,col3,col4 = st.columns(4)

col1.metric("Invoices Processed", total_invoices)
col2.metric("High Risk", high_risk)
col3.metric("Medium Risk", medium_risk)
col4.metric("Low Risk", low_risk)

# -----------------------------
# FILE UPLOAD
# -----------------------------

uploaded_file = st.file_uploader(
"Upload Invoice",
type=["png","jpg","jpeg","pdf"]
)

# -----------------------------
# PROCESS INVOICE
# -----------------------------

if uploaded_file is not None:

    if uploaded_file.type == "application/pdf":
        images = convert_from_bytes(uploaded_file.read())
        image = images[0]
    else:
        image = Image.open(uploaded_file)

    st.subheader("📄 Invoice Preview")
    st.image(image,use_container_width=True)

    # OCR
    st.subheader("🔍 Extracting Invoice Text")
    text = pytesseract.image_to_string(image)

    st.subheader("📝 Extracted Text")
    st.text_area("Invoice Data",text,height=250)

    # -------------------------
    # EXTRACT FIELDS
    # -------------------------

    invoice_match = re.search(r"Invoice\s*No[:\s]*([A-Z0-9\-]+)",text)
    invoice_number = invoice_match.group(1) if invoice_match else "Unknown"

    total_match = re.search(r"Total.*?([0-9,]+\.[0-9]{2})",text)
    total_amount = total_match.group(1) if total_match else "0"

    vendor_match = re.search(r"Billed\s*By[:\s]*(.*)",text)
    vendor = vendor_match.group(1) if vendor_match else "Unknown Vendor"

    st.subheader("📌 Extracted Fields")

    c1,c2,c3 = st.columns(3)

    c1.write(f"Invoice Number: {invoice_number}")
    c2.write(f"Vendor: {vendor}")
    c3.write(f"Amount: {total_amount}")

    # -------------------------
    # FRAUD DETECTION LOGIC
    # -------------------------

    warnings = []
    risk_score = 0

    # Duplicate detection
    for inv in st.session_state.invoice_db:
        if inv["invoice"] == invoice_number:
            warnings.append("⚠ Duplicate Invoice Detected")
            risk_score += 40

    # High value invoice
    try:
        amount = float(total_amount.replace(",",""))
        if amount > 1000000:
            warnings.append("⚠ High Value Invoice — Manual Review Required")
            risk_score += 30
    except:
        pass

    # GST check
    if "GST" not in text and "gst" not in text:
        warnings.append("⚠ GST Not Detected")
        risk_score += 20

    # Vendor pattern detection
    vendor_count = sum(1 for inv in st.session_state.invoice_db if inv["vendor"] == vendor)

    if vendor_count > 5:
        warnings.append("⚠ Vendor Appears Frequently — Check Vendor Risk")
        risk_score += 20

    # -------------------------
    # FRAUD RESULT
    # -------------------------

    st.subheader("🚨 Fraud Detection")

    if warnings:
        for w in warnings:
            st.error(w)
    else:
        st.success("No suspicious patterns detected")

    # -------------------------
    # RISK SCORE
    # -------------------------

    st.subheader("🤖 AI Risk Score")

    st.progress(min(risk_score,100))

    st.write(f"Risk Score: {risk_score}%")

    if risk_score > 60:
        st.error("High Risk Invoice")
    elif risk_score > 30:
        st.warning("Medium Risk Invoice")
    else:
        st.success("Low Risk Invoice")

    # -------------------------
    # SAVE INVOICE
    # -------------------------

    st.session_state.invoice_db.append({
        "invoice":invoice_number,
        "vendor":vendor,
        "amount":total_amount,
        "risk":risk_score
    })

# -----------------------------
# DATABASE VIEW
# -----------------------------

st.subheader("📁 Processed Invoice Database")

df = pd.DataFrame(st.session_state.invoice_db)

if not df.empty:
    st.dataframe(df,use_container_width=True)

# -----------------------------
# ANALYTICS
# -----------------------------

if not df.empty:

    st.subheader("📈 Fraud Risk Analytics")

    risk_counts = df["risk"].apply(
        lambda x: "High" if x>60 else "Medium" if x>30 else "Low"
    ).value_counts()

    st.bar_chart(risk_counts)

# -----------------------------
# DOWNLOAD REPORT
# -----------------------------

if not df.empty:

    csv = df.to_csv(index=False)

    st.download_button(
        label="Download Audit Report",
        data=csv,
        file_name="invoice_audit_report.csv",
        mime="text/csv"
    )

st.info("SmartAudit AI continuously analyzes invoice patterns to detect potential financial fraud.")


