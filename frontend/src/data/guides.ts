export interface Guide { slug: string; title: string; description: string; h1: string; tool: string; sections: { h: string; p: string[] }[] }

export const GUIDES: Guide[] = [
  {
    slug: 'bank-statement-pdf-to-excel', tool: 'bank-statement-to-excel', h1: 'How to convert a bank statement PDF to Excel',
    title: 'How to Convert a Bank Statement PDF to Excel (Step by Step)', description: 'A practical guide to turning a bank statement PDF into a clean Excel sheet, including what to check before you trust the numbers.',
    sections: [
      { h: 'Why copy-paste usually fails', p: ['Pasting from a PDF often merges columns or splits wrapped descriptions across rows. A converter that understands rows, dates and amounts avoids most of that.'] },
      { h: 'Steps', p: ['Download the statement as a PDF from your bank (digital PDFs convert best). Upload it, wait for extraction, then review the table: confirm dates, debit and credit columns, and any row marked for review.', 'Compare totals with the opening and closing balance printed on the statement. Edit mistakes in the table, then export.'] },
      { h: 'What to check before you rely on it', p: ['Look at the first and last rows, any row with a large amount, and rows flagged for balance mismatches. A single wrong digit changes totals, so spot-check against the PDF.'] },
    ],
  },
  {
    slug: 'scanned-bank-statement-transactions', tool: 'pdf-bank-statement-converter', h1: 'How to extract transactions from a scanned bank statement',
    title: 'Extract Transactions from a Scanned Bank Statement (OCR Guide)', description: 'How OCR reads a scanned bank statement, why digits get misread, and how balance checks help you catch errors.',
    sections: [
      { h: 'Scans are pictures', p: ['A scanned statement has no text to copy. OCR software recognises characters from the image, so quality of the scan matters more than anything else.'] },
      { h: 'Getting a better scan', p: ['Scan at 300 dpi, keep pages straight, use even lighting and avoid compression artefacts. Black text on a white background reads best.'] },
      { h: 'Use balances as a safety net', p: ['If every row has a running balance, an OCR error in an amount usually breaks the arithmetic. Rows where previous balance plus credit minus debit does not equal the balance are flagged for you to check.'] },
    ],
  },
  {
    slug: 'invoice-pdf-to-excel', tool: 'invoice-to-excel', h1: 'How to convert an invoice PDF into Excel',
    title: 'How to Convert an Invoice PDF into Excel (With Line Items)', description: 'Extract invoice number, dates, GSTIN, taxes and line items from a PDF invoice into a structured Excel workbook.',
    sections: [
      { h: 'What belongs in an invoice sheet', p: ['Keep header details (supplier, customer, number, dates, taxes, totals) separate from line items so each can be filtered and summed properly.'] },
      { h: 'GST invoices', p: ['Indian GST invoices add GSTIN, HSN/SAC codes and CGST, SGST or IGST amounts. Check that taxable value plus taxes equals the grand total, allowing for round-off.'] },
      { h: 'Verify the totals', p: ['Add the line totals yourself or use the check shown in the review screen. If they differ from the subtotal, find the row that is wrong.'] },
    ],
  },
  {
    slug: 'invoice-data-from-image', tool: 'invoice-image-to-excel', h1: 'How to extract invoice data from an image',
    title: 'How to Extract Invoice Data from a Photo or Image', description: 'Tips for photographing an invoice so OCR can read it, and how to correct the extracted fields.',
    sections: [
      { h: 'Take a readable photo', p: ['Place the invoice on a flat, plain surface, use daylight or an even lamp, and hold the phone directly above the page. Make sure all four corners and the totals are inside the frame.'] },
      { h: 'Review highlighted fields', p: ['Fields the OCR engine was unsure about are highlighted. Always compare amounts and tax IDs with the image.'] },
    ],
  },
  {
    slug: 'organize-receipts-in-excel', tool: 'receipt-to-excel', h1: 'How to organise receipt data in Excel',
    title: 'How to Organise Receipt Data in Excel', description: 'A simple structure for tracking receipts and expenses in a spreadsheet, plus how to batch-extract them from photos.',
    sections: [
      { h: 'A simple layout', p: ['One row per receipt: date, merchant, receipt number, subtotal, tax, total and payment method. Keep line items on a second sheet linked by receipt.'] },
      { h: 'Keep the originals', p: ['Store the receipt image or PDF alongside the spreadsheet. The spreadsheet is a summary; the original is the evidence.'] },
    ],
  },
  {
    slug: 'extract-tables-from-pdf', tool: 'pdf-table-extractor', h1: 'How to extract tables from a PDF',
    title: 'How to Extract Tables from a PDF into Excel or CSV', description: 'Why PDF tables are tricky, which kinds extract well, and how to clean the result.',
    sections: [
      { h: 'Tables with and without lines', p: ['Tables drawn with ruling lines are the easiest to detect. Tables that only use spacing can be detected too but are less reliable.'] },
      { h: 'Clean-up tips', p: ['Check header names, merged cells and rows that continue across pages. Keep identifiers like 00123 as text so leading zeros are not lost.'] },
    ],
  },
  {
    slug: 'common-ocr-errors', tool: 'invoice-image-to-excel', h1: 'Common OCR errors and how to correct them',
    title: 'Common OCR Errors in Financial Documents and How to Fix Them', description: 'The digit and symbol mix-ups OCR makes most often, and a checklist for catching them.',
    sections: [
      { h: 'Frequent mix-ups', p: ['OCR can confuse 0 and O, 1 and l or I, 5 and S, 8 and B, and commas with full stops. A comma read as a full stop can turn 2,000.00 into 2.000.00, which is why unusual number formats are flagged rather than silently repaired.'] },
      { h: 'A checklist', p: ['Compare totals, check that dates are valid, make sure balances add up, and re-scan pages that are blurry or skewed.'] },
    ],
  },
]
export const guideBySlug = (slug?: string) => GUIDES.find((g) => g.slug === slug)
