import io
from pypdf import PdfReader

def extract_text_from_pdf(pdf_bytes:bytes) -> str:
    """
    Extracts raw content from uploaded digital pdf byte stream
    Handles single and multi-page invoices
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        extracted_text = ""
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                extracted_text+=f"--- Page {page_num+1} ---\n{text}\n"
        if not extracted_text.strip():
            raise ValueError("No readable text found in PDF. File may be an image scan or corrupted.")
        return extracted_text
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF: {str(e)}")
