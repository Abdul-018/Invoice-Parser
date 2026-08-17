import os
from typing import List, Dict
from datetime import datetime
from google import genai
from google.genai import types
from schemas import InvoiceData
from pydantic import BaseModel, Field
import config

# Helper function to parse DD-MM-YYYY string into a datetime.date object
def parse_date_str(date_str: str):
    if not date_str:
        return datetime.today().date()
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").date()
    except ValueError:
        return datetime.today().date()

class BatchInvoiceResponse(BaseModel):
    invoices: List[InvoiceData]

def parse_multiple_invoices(invoices_text_map: Dict[str, str]) -> List[InvoiceData]:
    """
    Sends all invoice texts in a single prompt to Gemini Flash.
    
    invoices_text_map: Dict where key is filename and value is extracted text.
    """
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Build a single aggregated prompt string
    bundled_prompt = """Extract details for all the invoices provided below into structured JSON.
    CRITICAL DATE RULES:
    1. Parse written dates carefully (e.g., "July 8, 2011" -> "2011-07-08").
    2. All dates MUST follow YYYY-MM-DD format strictl
    \n\n"""
    for filename, raw_text in invoices_text_map.items():
        bundled_prompt += f"--- START INVOICE: {filename} ---\n"
        bundled_prompt += f"{raw_text.strip()[:3500]}\n"  # Limit each invoice text to avoid bloat
        bundled_prompt += f"--- END INVOICE: {filename} ---\n\n"

    response = client.models.generate_content(
        model='gemini-3.5-flash-lite',
        contents=bundled_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=BatchInvoiceResponse,
            temperature=0.0
        )
    )

    if hasattr(response, "parsed") and response.parsed:
        return response.parsed.invoices

    parsed_batch = BatchInvoiceResponse.model_validate_json(response.text)
    return parsed_batch.invoices

def parse_invoice_text(raw_text: str) -> InvoiceData:
    """
    Passes extracted invoice text to Gemini Flash with strict JSON schema constraints.
    """
    # Ensure API Key is explicitly passed to the client
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an expert accounts payable parser for Apex Logistics. 
    Extract all relevant invoice details from the raw document text below.
    Strictly enforce field data types and output structured JSON.
    CRITICAL DATE RULES:
    1. Parse written dates carefully (e.g., "July 8, 2011" -> "2011-07-08").
    2. All dates MUST follow YYYY-MM-DD format strictly.
    
    Document Raw Text:
    {raw_text}
    """

    response = client.models.generate_content(
        model='gemini-3.5-flash-lite',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=InvoiceData,
            temperature=0.0,
        )
    )

    # Use client response validation or JSON fallback
    if hasattr(response, "parsed") and response.parsed:
        return response.parsed

    return InvoiceData.model_validate_json(response.text)