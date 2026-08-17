import pytest
from pydantic import ValidationError
from schemas import InvoiceData, LineItem
from services.pdf_service import extract_text_from_pdf

def test_valid_invoice_schema():
    """Tests that InvoiceData validates valid fields and accepts DD-MM-YYYY dates."""
    data = {
        "vendor_name": "Apex Fuel Corp",
        "invoice_number": "INV-2026-001",
        "invoice_date": "12-08-2026",
        "due_date": "26-08-2026",
        "line_items": [
            {"description": "Diesel Fuel", "quantity": 100.0, "unit_price": 3.50, "total_price": 350.0}
        ],
        "subtotal": 350.0,
        "tax_amount": 35.0,
        "total_amount": 385.0
    }
    invoice = InvoiceData(**data)
    assert invoice.vendor_name == "Apex Fuel Corp"
    assert invoice.invoice_date == "12-08-2026"
    assert len(invoice.line_items) == 1
    assert invoice.line_items[0].total_price == 350.0

def test_line_item_defaults():
    """Verifies that optional fields in LineItem set appropriate defaults."""
    item = LineItem(description="Flat Toll Surcharge", total_price=15.0)
    assert item.quantity == 1.0  # Default quantity
    assert item.unit_price is None  # Default optional unit price

def test_schema_invalid_type():
    """Ensures Pydantic fails gracefully when passed an invalid data type."""
    data = {
        "vendor_name": "Test Vendor",
        "invoice_number": "123",
        "subtotal": "invalid_number_string",  # Should fail float validation
        "tax_amount": 0.0,
        "total_amount": 100.0
    }
    with pytest.raises(ValidationError):
        InvoiceData(**data)

def test_pdf_extraction_invalid_bytes():
    """Ensures pdf_service raises a RuntimeError when handling non-PDF bytes."""
    bad_bytes = b"This is plain text, not a PDF file."
    with pytest.raises(RuntimeError):
        extract_text_from_pdf(bad_bytes)