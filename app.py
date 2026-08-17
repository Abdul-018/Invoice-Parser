import streamlit as st
import json
from datetime import datetime, date
import pandas as pd

from services.pdf_service import extract_text_from_pdf
from services.llm_service import parse_invoice_text
from schemas import InvoiceData, LineItem

# ------------------------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Invoice Processing Dashboard",
    page_icon="🧾",
    layout="wide"
)

st.title("🧾 AI-Powered Invoice Processing Dashboard")
st.markdown("Upload a PDF vendor invoice to extract, verify, and export structured data.")

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def parse_date_str(date_input):
    """Safely converts string or date object into a datetime.date object."""
    if not date_input:
        return datetime.today().date()
    
    # If Pydantic or Gemini already returned a date/datetime object:
    if isinstance(date_input, date):
        return date_input
    if isinstance(date_input, datetime):
        return date_input.date()
        
    # If it's a string, attempt parsing with multiple formats
    if isinstance(date_input, str):
        for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(date_input.strip(), fmt).date()
            except ValueError:
                continue

    # Fallback to current date if parsing fails
    return datetime.today().date()

# ------------------------------------------------------------------------------
# Main Dashboard Layout
# ------------------------------------------------------------------------------
upload_col, display_col = st.columns([1, 2], gap="large")

with upload_col:
    st.subheader("1. Upload Invoice")
    uploaded_file = st.file_uploader("Select PDF File", type=["pdf"])

    if uploaded_file is not None:
        if st.button("Process Invoice", type="primary", use_container_width=True):
            with st.spinner("Extracting text and parsing invoice..."):
                try:
                    # Step 1: Extract text from PDF bytes
                    raw_bytes = uploaded_file.read()
                    extracted_text = extract_text_from_pdf(raw_bytes)
                    
                    # Step 2: Send extracted text to Gemini API
                    parsed_data = parse_invoice_text(extracted_text)
                    
                    # Step 3: Save results in session state
                    st.session_state["raw_text"] = extracted_text
                    st.session_state["parsed_invoice"] = parsed_data
                    st.success("Invoice processed successfully!")
                except Exception as e:
                    st.error(f"Extraction Error: {str(e)}")

    if "raw_text" in st.session_state:
        with st.expander("View Extracted Raw Text"):
            st.text_area("PDF Text Layer", st.session_state["raw_text"], height=250)

with display_col:
    st.subheader("2. Review & Verify Extracted Data")

    if "parsed_invoice" in st.session_state:
        parsed: InvoiceData = st.session_state["parsed_invoice"]

        with st.form("invoice_verification_form"):
            # Header Fields
            c1, c2 = st.columns(2)
            with c1:
                vendor_name = st.text_input("Vendor Name", value=parsed.vendor_name)
                inv_num = st.text_input("Invoice Number", value=parsed.invoice_number)
            with c2:
                inv_date_obj = st.date_input("Invoice Date", value=parse_date_str(parsed.invoice_date), format="DD-MM-YYYY")
                due_date_obj = st.date_input("Due Date", value=parse_date_str(parsed.due_date), format="DD-MM-YYYY")

            st.divider()
            st.markdown("##### Line Items")

            # Convert line items to Pandas DataFrame for Streamlit interactive data editor
            items_data = [item.model_dump() for item in parsed.line_items]
            df_items = pd.DataFrame(items_data if items_data else [{"description": "", "quantity": 1.0, "unit_price": 0.0, "total_price": 0.0}])

            edited_df = st.data_editor(
                df_items,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "description": st.column_config.TextColumn("Description", required=True),
                    "quantity": st.column_config.NumberColumn("Quantity", min_value=0.0, step=0.1, default=1.0),
                    "unit_price": st.column_config.NumberColumn("Unit Price ($)", min_value=0.0, step=0.01),
                    "total_price": st.column_config.NumberColumn("Total Price ($)", min_value=0.0, step=0.01, required=True),
                }
            )

            st.divider()
            st.markdown("##### Financial Summary")

            # Financial Summaries
            f1, f2, f3 = st.columns(3)
            with f1:
                subtotal = st.number_input("Subtotal ($)", value=float(parsed.subtotal), step=0.01)
            with f2:
                tax_amount = st.number_input("Tax ($)", value=float(parsed.tax_amount), step=0.01)
            with f3:
                total_amount = st.number_input("Total Amount ($)", value=float(parsed.total_amount), step=0.01)

            save_submitted = st.form_submit_button("Save & Validate Changes", type="primary", use_container_width=True)

            if save_submitted:
                # Re-construct LineItems from edited DataFrame
                updated_items = [
                    LineItem(
                        description=row["description"],
                        quantity=row.get("quantity"),
                        unit_price=row.get("unit_price"),
                        total_price=float(row["total_price"])
                    )
                    for _, row in edited_df.iterrows()
                    if row["description"].strip()
                ]

                # Update verified model state
                verified_invoice = InvoiceData(
                    vendor_name=vendor_name,
                    invoice_number=inv_num,
                    invoice_date=inv_date_obj.strftime("%d-%m-%Y"),
                    due_date=due_date_obj.strftime("%d-%m-%Y"),
                    line_items=updated_items,
                    subtotal=subtotal,
                    tax_amount=tax_amount,
                    total_amount=total_amount
                )

                st.session_state["verified_invoice"] = verified_invoice
                st.success("Verification complete!")

        # Export Section
        if "verified_invoice" in st.session_state:
            st.divider()
            st.subheader("3. Export Validated Data")
            
            export_json = st.session_state["verified_invoice"].model_dump_json(indent=2)
            
            st.download_button(
                label="📥 Download Structured JSON",
                data=export_json,
                file_name=f"invoice_{st.session_state['verified_invoice'].invoice_number}.json",
                mime="application/json",
                use_container_width=True
            )
    else:
        st.info("Please upload and process an invoice to view the extracted data.")