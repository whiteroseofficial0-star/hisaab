"""Synthetic, fictional test documents. No real people, banks or account numbers."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pdfplumber
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

BANK_ROWS = [
    # date, narration, ref, value date, debit, credit
    ("01/04/2025", "UPI-FICTIONAL GROCERS-9876543210", "0000987654321", "01/04/2025", 450.00, None),
    ("02/04/2025", "NEFT CR-TEST EMPLOYER LTD SALARY APRIL", "N123456789012", "02/04/2025", None, 50000.00),
    ("03/04/2025", "ATM WDL CHQ NO 123456 SAMPLE ROAD", "0000000123456", "03/04/2025", 2000.00, None),
    ("05/04/2025", "IMPS-DEMO RENT PAYMENT", "0000555566667", "05/04/2025", 12500.50, None),
    ("08/04/2025", "INTEREST CREDIT", "0000000000000", "08/04/2025", None, 125.75),
    ("10/04/2025", "POS 4000XXXXXX1111 TEST CAFE", "0000111122223", "10/04/2025", 1234.00, None),
]
OPENING = 10000.00


def _fmt(x):
    return f"{x:,.2f}"


def make_bank_statement_pdf(path: Path, rows=BANK_ROWS, opening=OPENING, wrap_second=True) -> list[dict]:
    """Two-page text statement with repeated header, a wrapped narration and a continued row."""
    c = canvas.Canvas(str(path), pagesize=A4)
    W, H = A4
    xs = {"date": 30, "narr": 82, "ref": 228, "vdate": 305, "debit": 420, "credit": 492, "bal": 566}  # debit/credit/bal = right edges

    def header(y):
        c.setFont("Helvetica-Bold", 8)
        c.drawString(xs["date"], y, "Date")
        c.drawString(xs["narr"], y, "Narration")
        c.drawString(xs["ref"], y, "Chq./Ref.No.")
        c.drawString(xs["vdate"], y, "Value Dt")
        c.drawRightString(xs["debit"], y, "Withdrawal Amt.")
        c.drawRightString(xs["credit"], y, "Deposit Amt.")
        c.drawRightString(xs["bal"], y, "Closing Balance")
        c.setFont("Helvetica", 8)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, H - 50, "Sample National Bank (Fictional)")
    c.setFont("Helvetica", 9)
    c.drawString(40, H - 68, "Statement of Account")
    c.drawString(40, H - 82, "Account Name: Test Customer")
    c.drawString(40, H - 96, "Account No: 555500001234")
    c.drawString(40, H - 110, "Statement Period: 01/04/2025 to 30/04/2025")
    c.drawString(40, H - 124, f"Opening Balance: {_fmt(opening)}")
    y = H - 160
    header(y)
    y -= 16
    balance = opening
    out = []
    for i, (d, narr, ref, vd, dr, cr) in enumerate(rows):
        balance = balance - (dr or 0) + (cr or 0)
        if i == 3:  # page break before the 4th row to test cross-page headers
            c.setFont("Helvetica", 7)
            c.drawString(40, 30, "Page 1 of 2  This is a computer generated statement")
            c.showPage()
            c.setFont("Helvetica", 8)
            y = H - 60
            header(y)
            y -= 16
        c.setFont("Helvetica", 9)
        c.drawString(xs["date"], y, d)
        parts = textwrap.wrap(narr, 26)
        c.drawString(xs["narr"], y, parts[0])
        c.drawString(xs["ref"], y, ref)
        c.drawString(xs["vdate"], y, vd)
        if dr is not None:
            c.drawRightString(xs["debit"], y, _fmt(dr))
        if cr is not None:
            c.drawRightString(xs["credit"], y, _fmt(cr))
        c.drawRightString(xs["bal"], y, _fmt(balance))
        y -= 12
        if len(parts) > 1 and wrap_second:
            c.drawString(xs["narr"], y, " ".join(parts[1:]))
            y -= 12
        y -= 6
        out.append({"date": d, "debit": dr, "credit": cr, "balance": round(balance, 2), "narr": narr})
    y -= 10
    c.drawString(30, y, f"Closing Balance: {_fmt(balance)}")
    c.setFont("Helvetica", 7)
    c.drawString(40, 30, "Page 2 of 2  This is a computer generated statement")
    c.save()
    return out


def pdf_to_scanned(src: Path, dst: Path, dpi=250, rotate_deg=0.0) -> None:
    """Rasterise a PDF into an image-only PDF (no text layer), optionally skewed."""
    imgs = []
    with pdfplumber.open(src) as pdf:
        for p in pdf.pages:
            im = p.to_image(resolution=dpi).original.convert("RGB")
            if rotate_deg:
                im = im.rotate(rotate_deg, expand=False, fillcolor=(255, 255, 255))
            imgs.append(im)
    imgs[0].save(dst, "PDF", resolution=dpi, save_all=True, append_images=imgs[1:])


def pdf_page_to_png(src: Path, dst: Path, dpi=200, page=0) -> None:
    with pdfplumber.open(src) as pdf:
        pdf.pages[page].to_image(resolution=dpi).original.convert("RGB").save(dst, "PNG")


def make_invoice_pdf(path: Path) -> None:
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    st = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=A4)
    el = [
        Paragraph("Sample Traders Pvt Ltd (Fictional)", st["Heading2"]),
        Paragraph("12 Test Street, Demo Nagar, Pune 411001", st["Normal"]),
        Paragraph("GSTIN: 27ABCDE1234F1Z5", st["Normal"]),
        Spacer(1, 8),
        Paragraph("TAX INVOICE", st["Heading3"]),
        Paragraph("Invoice No: INV-2025-001", st["Normal"]),
        Paragraph("Invoice Date: 05/04/2025", st["Normal"]),
        Paragraph("Due Date: 20/04/2025", st["Normal"]),
        Paragraph("PO Number: PO-7788", st["Normal"]),
        Spacer(1, 8),
        Paragraph("Bill To:", st["Normal"]),
        Paragraph("Demo Customer LLP", st["Normal"]),
        Paragraph("99 Example Road, Mumbai 400001", st["Normal"]),
        Paragraph("GSTIN: 27PQRSX9876L1Z2", st["Normal"]),
        Spacer(1, 10),
    ]
    data = [["No", "Description", "HSN/SAC", "Qty", "Rate", "Amount"],
            ["1", "Widget A", "8471", "2", "500.00", "1,000.00"],
            ["2", "Service B", "9983", "1", "1,500.00", "1,500.00"]]
    t = Table(data)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    el += [t, Spacer(1, 10)]
    for line in ["Subtotal: 2,500.00", "CGST @9%: 225.00", "SGST @9%: 225.00", "Round off: 0.00",
                 "Grand Total: 2,950.00", "Payment Terms: Net 15 days"]:
        el.append(Paragraph(line, st["Normal"]))
    doc.build(el)


def make_receipt_pdf(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=(230, 420))
    c.setFont("Courier", 8)
    y = 400
    for line in ["FICTIONAL CAFE", "Bill No: 4521", "Date: 12/05/2025 14:32", "GSTIN: 27AAAAA0000A1Z5",
                 "----------------------------", "Masala Tea 2 20.00 40.00", "Veg Sandwich 1 90.00 90.00",
                 "Cold Coffee 1 70.00 70.00", "----------------------------", "Subtotal 200.00",
                 "CGST 2.5% 5.00", "SGST 2.5% 5.00", "Total 210.00", "Paid by UPI", "Thank you"]:
        c.drawString(10, y, line)
        y -= 14
    c.save()


def make_table_pdf(path: Path) -> None:
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    st = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=A4)
    data = [["Item", "Stock", "Price"], ["Pen", "120", "5.50"], ["Notebook", "45", "42.00"], ["=SUM(1,2)", "3", "9.99"]]
    t = Table(data)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    doc.build([Paragraph("Inventory (fictional)", st["Heading2"]), t])
