import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

from services.pdf_service import extract_text_from_pdf
from services.llm_service import parse_multiple_invoices

load_dotenv()

def batch_process_single_api_call(folder_path: str, output_file: str = "batch_results.json"):
    dir_path = Path(folder_path)
    if not dir_path.exists() or not dir_path.is_dir():
        print(f"❌ Error: Directory '{folder_path}' does not exist.")
        return

    pdf_files = list(dir_path.glob("*.pdf"))
    if not pdf_files:
        print(f"⚠️ No PDF files found in '{folder_path}'.")
        return

    print(f"\n🚀 Found {len(pdf_files)} PDFs in '{folder_path}'.")
    print("1. Extracting text from all PDFs locally...")
    
    t0 = time.time()
    invoices_map = {}
    for pdf in pdf_files:
        try:
            raw_text = extract_text_from_pdf(pdf.read_bytes())
            if raw_text.strip():
                invoices_map[pdf.name] = raw_text
            else:
                print(f"⚠️ Skipping {pdf.name} (No text layer found)")
        except Exception as e:
            print(f"❌ Error reading {pdf.name}: {e}")

    t1 = time.time()
    print(f"   Done reading files in {t1 - t0:.2f} seconds.")

    print(f"2. Sending ALL {len(invoices_map)} invoices to Gemini in ONE single API call...")
    
    try:
        results = parse_multiple_invoices(invoices_map)
        total_time = time.time() - t1

        # Convert Pydantic objects to standard dictionaries for JSON output
        results_dict = [inv.model_dump(mode="json") for inv in results]

        # Save output to disk
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results_dict, f, indent=2)

        print("\n" + "=" * 50)
        print(" BATCH PARSING SUMMARY (SINGLE API CALL) ")
        print("=" * 50)
        print(f" Total PDFs Found : {len(pdf_files)}")
        print(f" Parsed Invoices  : {len(results_dict)}")
        print(f" API Elapsed Time : {total_time:.2f} seconds")
        print(f" Avg Time / File  : {total_time / len(pdf_files):.2f} seconds")
        print(f" Results Saved    : {Path(output_file).resolve()}")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Failed to process batch request: {e}")

if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Warning: GEMINI_API_KEY environment variable is missing.")
        
    target_folder = input("Enter path to invoice folder (e.g., ./invoices): ").strip()
    batch_process_single_api_call(target_folder)