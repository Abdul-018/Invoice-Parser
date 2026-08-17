import random
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_invoice(inv_num):
    filepath = f"./invoices/invoice_{inv_num}.pdf"
    c = canvas.Canvas(filepath, pagesize=letter)

    # Header
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 740, "INVOICE")

    c.setFont("Helvetica", 10)
    c.drawString(400, 740, f"Invoice #: INV-{inv_num}")
    c.drawString(400, 725, "Date: 2026-08-17")
    c.drawString(400, 710, "Due Date: 2026-09-17")

    # Client Info
    c.drawString(50, 690, "Bill To:")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 675, f"Client Company {inv_num} LLC")

    # Table Header
    c.line(50, 640, 550, 640)
    c.drawString(50, 625, "Description")
    c.drawString(300, 625, "Qty")
    c.drawString(380, 625, "Unit Price")
    c.drawString(480, 625, "Total")
    c.line(50, 615, 550, 615)

    # Line items
    y = 595
    subtotal = 0.0
    items = ["Consulting", "Design", "Software License", "Maintenance", "Support"]

    for i in range(random.randint(1, 4)):
        desc = random.choice(items)
        qty = random.randint(1, 10)
        price = round(random.uniform(50.0, 500.0), 2)
        total = round(qty * price, 2)
        subtotal += total

        c.setFont("Helvetica", 10)
        c.drawString(50, y, desc)
        c.drawString(300, y, str(qty))
        c.drawString(380, y, f"£{price:.2f}")
        c.drawString(480, y, f"£{total:.2f}")
        y -= 20

    # Totals
    tax = round(subtotal * 0.08, 2)
    grand_total = round(subtotal + tax, 2)

    c.line(50, y, 550, y)
    y -= 20
    c.drawString(380, y, "Subtotal:")
    c.drawString(480, y, f"£{subtotal:.2f}")
    y -= 15
    c.drawString(380, y, "Tax (8%):")
    c.drawString(480, y, f"£{tax:.2f}")
    y -= 15
    c.setFont("Helvetica-Bold", 10)
    c.drawString(380, y, "Total Due:")
    c.drawString(480, y, f"£{grand_total:.2f}")

    c.save()


# Generate 5 sample invoices
for i in range(1001, 1101):
    generate_invoice(i)
print("Generated 100 PDF invoices successfully.")