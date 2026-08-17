from pydantic import BaseModel, Field 
from typing import List, Optional
from datetime import date

class LineItem(BaseModel):
    """Schema for individual itemised billing breakdown"""
    description: str = Field(description="Description of the item, service, fuel or toll")
    quantity: Optional[float] = Field(default=1.0, description="Quantity billed")
    unit_price: Optional[float] = Field(default=None, description="The price of each unit")
    total_price: float = Field(description="The total price of the products")

class InvoiceData(BaseModel):
    vendor_name: str = Field(description="Name of issuing vendor")
    invoice_number: str = Field(description="The unique reference of the invoice")
    invoice_date: Optional[date] = Field(default=None, description="The issue date of the invoice [DD-MM-YYYY]")
    due_date: Optional[date] = Field(default=None, description="The date that the money is due [DD-MM-YYYY]")
    line_items: List[LineItem] = Field(default_factory=list, description="List of itemised billing records[cite: 1]")
    subtotal: float = Field(description="Subtotal amount before tax[cite: 1]")
    tax_amount: float = Field(description="Tax amount charged[cite: 1]")
    total_amount: float = Field(description="Final total balance due[cite: 1]")