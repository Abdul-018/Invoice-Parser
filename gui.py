import os
import threading
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox
from dotenv import load_dotenv

from services.pdf_service import extract_text_from_pdf
from services.llm_service import parse_multiple_invoices

load_dotenv()

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class InvoiceParserApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("Apex Logistics — Fast Invoice Parser")
        self.geometry("800x650")
        self.minsize(700, 550)
        self.selected_files = []
        self.parsed_data = []

        # Configure Grid Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Build UI Sections
        self._create_header()
        self._create_main_content()
        self._create_footer()

    def _create_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=25, pady=(20, 10), sticky="ew")

        title = ctk.CTkLabel(
            header_frame,
            text="Apex Invoice Batch Parser",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold")
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Extract and structure PDF invoice data using AI",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="gray"
        )
        subtitle.pack(anchor="w")

    def _create_main_content(self):
        main_frame = ctk.CTkFrame(self, corner_radius=12)
        main_frame.grid(row=1, column=0, padx=25, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)  # Allow file list box to expand

        # File Selection Bar
        file_bar = ctk.CTkFrame(main_frame, fg_color="transparent")
        file_bar.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        file_bar.grid_columnconfigure(0, weight=1)

        self.select_btn = ctk.CTkButton(
            file_bar,
            text="📁 Select PDF Invoices",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            command=self.select_files
        )
        self.select_btn.grid(row=0, column=0, sticky="ew")

        self.file_count_label = ctk.CTkLabel(
            file_bar,
            text="No files selected",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.file_count_label.grid(row=1, column=0, sticky="w", pady=(8, 0))

        # Selected Files Preview Box
        self.file_box = ctk.CTkTextbox(
            main_frame,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            state="disabled",
            wrap="none"
        )
        self.file_box.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        # Processing & Progress Section
        process_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        process_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")
        process_frame.grid_columnconfigure(0, weight=1)

        self.run_btn = ctk.CTkButton(
            process_frame,
            text="⚡ Process Invoices",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            fg_color="#2FA572",
            hover_color="#1E7852",
            command=self.start_processing_thread,
            state="disabled"
        )
        self.run_btn.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        self.status_label = ctk.CTkLabel(
            process_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self.status_label.grid(row=1, column=0, sticky="w", pady=(0, 6))

        self.progress_bar = ctk.CTkProgressBar(process_frame, height=10)
        self.progress_bar.grid(row=2, column=0, sticky="ew")
        self.progress_bar.set(0)

    def _create_footer(self):
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=2, column=0, padx=25, pady=(0, 20), sticky="ew")
        footer_frame.grid_columnconfigure(0, weight=1)

        self.export_btn = ctk.CTkButton(
            footer_frame,
            text="💾 Export Results to CSV",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            fg_color="#1F6AA5",
            hover_color="#144870",
            command=self.export_csv,
            state="disabled"
        )
        self.export_btn.grid(row=0, column=0, sticky="ew")

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        if files:
            self.selected_files = list(files)
            self.file_count_label.configure(
                text=f"Selected {len(self.selected_files)} file(s)",
                text_color=("black", "white")
            )
            self.run_btn.configure(state="normal")

            # Update File Preview Textbox
            self.file_box.configure(state="normal")
            self.file_box.delete("1.0", "end")
            for f in self.selected_files:
                self.file_box.insert("end", f"📄  {os.path.basename(f)}\n")
            self.file_box.configure(state="disabled")

    def start_processing_thread(self):
        threading.Thread(target=self.process_invoices, daemon=True).start()

    def process_invoices(self):
        self.run_btn.configure(state="disabled")
        self.select_btn.configure(state="disabled")
        self.status_label.configure(text="Reading PDF files...")
        self.progress_bar.set(0.2)

        invoices_map = {}
        for filepath in self.selected_files:
            filename = os.path.basename(filepath)
            with open(filepath, "rb") as f:
                raw_text = extract_text_from_pdf(f.read())
                if raw_text.strip():
                    invoices_map[filename] = raw_text

        self.status_label.configure(text="Sending batch request to Gemini API...")
        self.progress_bar.set(0.6)

        try:
            results = parse_multiple_invoices(invoices_map)
            self.parsed_data = [inv.model_dump(mode="json") for inv in results]

            self.progress_bar.set(1.0)
            self.status_label.configure(text=f"✅ Successfully parsed {len(results)} invoices!")
            self.export_btn.configure(state="normal")
            messagebox.showinfo("Success", f"Parsed {len(results)} invoices in 1 API call!")
        except Exception as e:
            self.status_label.configure(text="❌ Error during processing")
            messagebox.showerror("Error", str(e))

        self.select_btn.configure(state="normal")

    def export_csv(self):
        if not self.parsed_data:
            return
            
        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv", 
            filetypes=[("CSV Files", "*.csv")]
        )
        if save_path:
            flattened_rows = []
            
            # Unpack nested line items into individual spreadsheet rows
            for invoice in self.parsed_data:
                line_items = invoice.get("line_items", [])
                
                if line_items:
                    for item in line_items:
                        flattened_rows.append({
                            "vendor_name": invoice.get("vendor_name"),
                            "invoice_number": invoice.get("invoice_number"),
                            "invoice_date": invoice.get("invoice_date"),
                            "due_date": invoice.get("due_date"),
                            "description": item.get("description"),
                            "quantity": item.get("quantity"),
                            "unit_price": item.get("unit_price"),
                            "total_price": item.get("total_price"),
                            "subtotal": invoice.get("subtotal"),
                            "tax_amount": invoice.get("tax_amount"),
                            "total_amount": invoice.get("total_amount"),
                        })
                else:
                    # Fallback for invoices parsed without line items
                    flattened_rows.append({
                        "vendor_name": invoice.get("vendor_name"),
                        "invoice_number": invoice.get("invoice_number"),
                        "invoice_date": invoice.get("invoice_date"),
                        "due_date": invoice.get("due_date"),
                        "description": None,
                        "quantity": None,
                        "unit_price": None,
                        "total_price": None,
                        "subtotal": invoice.get("subtotal"),
                        "tax_amount": invoice.get("tax_amount"),
                        "total_amount": invoice.get("total_amount"),
                    })

            df = pd.DataFrame(flattened_rows)
            df.to_csv(save_path, index=False)
            messagebox.showinfo("Export Successful", f"Saved flattened CSV to:\n{save_path}")


if __name__ == "__main__":
    app = InvoiceParserApp()
    app.mainloop()