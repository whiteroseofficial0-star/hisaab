import type { FileKind, ToolKey } from '../types'

export interface ToolPageDef {
  slug: string
  tool: ToolKey
  name: string
  title: string
  description: string
  h1: string
  intro: string
  accept: FileKind[]
  multiple: boolean
  formats: string
  steps: string[]
  details: { h: string; p: string }[]
  limitations: string[]
  faqs: { q: string; a: string }[]
  related: string[]
  guide?: string
}

export const TOOLS: ToolPageDef[] = [
  {
    slug: 'bank-statement-to-excel', tool: 'bank_statement', name: 'Bank statement to Excel', accept: ['pdf'], multiple: false, formats: 'PDF (digital or scanned)',
    title: 'Bank Statement to Excel Converter (PDF to XLSX/CSV) | Hisaab',
    description: 'Convert a bank statement PDF into an editable transaction table, then export to Excel or CSV. Handles digital and scanned statements with OCR. Review before you download.',
    h1: 'Convert a Bank Statement to Excel',
    intro: 'Upload a bank statement PDF and Hisaab reads the transactions into an editable table: dates, descriptions, references, debits, credits and balances. Fix anything that looks off, then download a real .xlsx or .csv file.',
    steps: ['Upload your statement PDF (digital or scanned).', 'Review the transaction table. Rows that need attention are marked "Check".', 'Edit, add or delete rows, then download Excel or CSV.'],
    details: [
      { h: 'What you get in the Excel file', p: 'A Transactions sheet with real date and number cells, header formatting, filters, a frozen header row and debit/credit totals, plus a Summary sheet with statement details such as masked account number, period and opening and closing balances.' },
      { h: 'How reconciliation works', p: 'Hisaab checks each running balance against the previous balance plus credits minus debits and compares opening and closing balances when the statement shows them. Banks use different conventions, so a mismatch is a prompt to compare with the original, not proof of an error.' },
    ],
    limitations: ['Amounts must show two decimals (for example 1,250.00).', 'Numeric dates are read as DD/MM/YYYY.', 'Password-protected PDFs are not supported; remove the password first.', 'Statements in unusual layouts may need more manual correction.'],
    faqs: [
      { q: 'Does it work on scanned statements?', a: 'Yes. Pages without selectable text are read with Tesseract OCR. OCR can misread digits, so rows with low confidence are flagged and balances are cross-checked.' },
      { q: 'Are my edits included in the download?', a: 'Yes. Excel and CSV files are generated from the table as it is after your edits, not from the original extraction.' },
      { q: 'Is my statement sent to an AI service?', a: 'No. Processing happens on the Hisaab server with open-source tools, and files expire automatically.' },
    ],
    related: ['pdf-bank-statement-converter', 'pdf-table-extractor'], guide: 'bank-statement-pdf-to-excel',
  },
  {
    slug: 'pdf-bank-statement-converter', tool: 'bank_statement', name: 'PDF bank statement converter', accept: ['pdf'], multiple: false, formats: 'PDF',
    title: 'PDF Bank Statement Converter: Digital and Scanned | Hisaab',
    description: 'A PDF bank statement converter that tells you how each page was read (text or OCR), flags uncertain rows and reconciles balances before export.',
    h1: 'PDF Bank Statement Converter',
    intro: 'This converter is built around transparency: for every page you can see whether the text came from the PDF itself or from OCR, and every row carries warnings when something could not be verified.',
    steps: ['Choose a bank statement PDF.', 'Check the page-by-page result and any warnings.', 'Correct the table and export to Excel or CSV.'],
    details: [
      { h: 'Digital PDFs versus scans', p: 'A digital PDF contains selectable text, which is read directly and is usually very accurate. A scan is just a picture of a page, so it goes through image clean-up (straightening and contrast) and OCR, which is less certain.' },
      { h: 'Wrapped descriptions and multi-page statements', p: 'Long narrations that wrap onto a second line are joined to the right transaction, and repeated table headers on later pages are recognised so rows continuing across pages are kept together.' },
    ],
    limitations: ['Only the first 40 pages are accepted by default (configurable when self-hosting).', 'Statements sorted newest-first are flagged because balances will not follow row order.', 'Merged or heavily decorated layouts may reduce accuracy.'],
    faqs: [
      { q: 'What if a debit or credit cannot be decided?', a: 'Hisaab does not guess. The amount is left unassigned, the row is flagged, and the original line is kept so you can fill it in.' },
      { q: 'Which banks are supported?', a: 'The parser is layout-based rather than bank-specific, so it can work with many statements, but support for any particular bank is not guaranteed. Try your statement and review the result.' },
    ],
    related: ['bank-statement-to-excel', 'pdf-to-csv'], guide: 'scanned-bank-statement-transactions',
  },
  {
    slug: 'invoice-to-excel', tool: 'invoice', name: 'Invoice PDF to Excel', accept: ['pdf', 'jpeg', 'png', 'webp'], multiple: false, formats: 'PDF, JPG, PNG, WebP',
    title: 'Invoice PDF to Excel: Extract Invoice Details and Line Items | Hisaab',
    description: 'Extract supplier, customer, GSTIN, invoice number, dates, taxes, totals and line items from an invoice PDF, review them, and export to Excel or CSV.',
    h1: 'Convert an Invoice PDF to Excel',
    intro: 'Hisaab reads digital and scanned invoices, filling in invoice details and a separate line-item table. It supports common Indian GST invoices (GSTIN, HSN/SAC, CGST, SGST, IGST) and generic invoices.',
    steps: ['Upload the invoice PDF.', 'Check the invoice fields and line items next to the original.', 'Fix any value, then export Excel (two sheets plus a summary) or CSV.'],
    details: [
      { h: 'Totals checks', p: 'Line totals are compared with the subtotal, and subtotal plus taxes and charges is compared with the grand total. A warning tells you which figures disagree; nothing is changed automatically.' },
      { h: 'Names and addresses', p: 'Supplier and customer blocks are inferred from the page layout, so they are shown as suggestions to verify rather than certain facts.' },
    ],
    limitations: ['One invoice per upload.', 'Tax-inclusive price lists may trigger total warnings.', 'Line items without clear columns may need to be added by hand.'],
    faqs: [
      { q: 'Can I extract several invoices at once?', a: 'Not yet; upload one invoice at a time.' },
      { q: 'Does it work for non-Indian invoices?', a: 'Yes for generic layouts. GST-specific fields simply stay empty when they are not present.' },
    ],
    related: ['invoice-image-to-excel', 'receipt-to-excel'], guide: 'invoice-pdf-to-excel',
  },
  {
    slug: 'invoice-image-to-excel', tool: 'invoice', name: 'Invoice image to Excel', accept: ['jpeg', 'png', 'webp'], multiple: false, formats: 'JPG, PNG, WebP',
    title: 'Invoice Image to Excel: Photo or Scan to Spreadsheet | Hisaab',
    description: 'Turn a photographed or scanned invoice (JPG, PNG, WebP) into editable invoice fields and line items with OCR, then export to Excel or CSV.',
    h1: 'Convert an Invoice Image to Excel',
    intro: 'Upload a photo or scan of an invoice. Hisaab straightens and enhances the image, reads it with OCR, and shows the original beside the extracted fields so you can correct anything the OCR got wrong.',
    steps: ['Upload a JPG, PNG or WebP image of the invoice.', 'Compare the extracted fields with the image; low-confidence fields are highlighted.', 'Edit and export to Excel or CSV.'],
    details: [
      { h: 'Getting a readable photo', p: 'Photograph the page flat, in even light, filling the frame. Avoid shadows across the text and keep the phone parallel to the page. Very small, blurry or dark images are rejected with an explanation.' },
      { h: 'File checks', p: 'The real image format is checked from the file contents, not only the file name, and very small images are refused because they cannot be read reliably.' },
    ],
    limitations: ['OCR is never 100% accurate; always compare amounts with the image.', 'Handwritten invoices are generally not readable.', 'Photos taken at a steep angle may not be straightened fully.'],
    faqs: [
      { q: 'What if the image is rotated?', a: 'Small tilts and phone orientation are corrected automatically. If the result is still wrong, rotate the image and upload again.' },
      { q: 'Why is a field highlighted?', a: 'The OCR engine reported low confidence for that line. It may still be right; it is just worth a look.' },
    ],
    related: ['invoice-to-excel', 'receipt-to-excel'], guide: 'invoice-data-from-image',
  },
  {
    slug: 'receipt-to-excel', tool: 'receipt', name: 'Receipt to Excel', accept: ['pdf', 'jpeg', 'png', 'webp'], multiple: true, formats: 'PDF, JPG, PNG, WebP (up to 10 files)',
    title: 'Receipt to Excel: Batch Extract Receipts and Expense Bills | Hisaab',
    description: 'Upload receipts and expense bills as photos or PDFs, extract merchant, date, tax and total into one table, review, and export to Excel or CSV.',
    h1: 'Extract Receipts and Expense Bills to Excel',
    intro: 'Upload up to ten receipts at once. Each file is processed independently into one row (merchant, date, subtotal, tax, discount, total, payment method) with an optional line-item table. Failed files are listed instead of silently dropped.',
    steps: ['Upload one or more receipt photos or PDFs.', 'Review the one-row-per-receipt table and the line items.', 'Export the whole batch to Excel or CSV.'],
    details: [
      { h: 'Batch behaviour', p: 'If one file cannot be read, the others still succeed and the unreadable file is named in the warnings so you can retake the photo.' },
      { h: 'Not an accounting decision', p: 'Hisaab extracts what is printed on the receipt. It does not decide whether something is a business expense or claim tax credit; you decide.' },
    ],
    limitations: ['Thermal-paper receipts that have faded are hard to read.', 'Crumpled or curved receipts reduce accuracy.', 'Line items are best-effort and may need correction.'],
    faqs: [
      { q: 'Does it categorise expenses?', a: 'No. Categories are not guessed, so you will not get a wrong category quietly.' },
      { q: 'What is the file limit?', a: 'Ten files per batch and 20 MB per file by default.' },
    ],
    related: ['invoice-image-to-excel', 'pdf-table-extractor'], guide: 'organize-receipts-in-excel',
  },
  {
    slug: 'pdf-table-extractor', tool: 'tables', name: 'PDF table extractor', accept: ['pdf'], multiple: false, formats: 'PDF',
    title: 'PDF Table Extractor: Pull Tables from PDF into Excel | Hisaab',
    description: 'Detect every table in a PDF, edit headers and cells, choose which tables to keep, and export them to Excel sheets or CSV files.',
    h1: 'Extract Tables from a PDF',
    intro: 'Hisaab finds the tables in a PDF and shows each one separately. Rename columns, fix cells, tick the tables you want, and export them as separate Excel sheets or CSV files.',
    steps: ['Upload a PDF that contains tables.', 'Review each detected table; untick the ones you do not need.', 'Download Excel (one sheet per table) or CSV.'],
    details: [
      { h: 'Ruled and unruled tables', p: 'Tables drawn with lines are detected most reliably. Tables aligned only by spacing are tried as a fallback with stricter checks to avoid mistaking paragraphs for tables.' },
      { h: 'Scanned PDFs', p: 'Scanned pages are read with OCR and split into columns by spacing. This is approximate and labelled as such.' },
    ],
    limitations: ['Merged cells and nested tables are flattened.', 'Tables spanning pages arrive as separate tables.', 'Numbers with leading zeros are kept as text on purpose.'],
    faqs: [
      { q: 'Why are some numbers text in Excel?', a: 'Values such as 00123 or long digit strings are kept as text so they are not altered. Clear decimals and comma-grouped numbers become real numbers.' },
    ],
    related: ['pdf-to-csv', 'bank-statement-to-excel'], guide: 'extract-tables-from-pdf',
  },
  {
    slug: 'pdf-to-csv', tool: 'tables', name: 'PDF to CSV', accept: ['pdf'], multiple: false, formats: 'PDF',
    title: 'PDF to CSV Converter: Export PDF Tables as CSV | Hisaab',
    description: 'Convert tables in a PDF to clean UTF-8 CSV files with safe escaping, ready for Excel, Google Sheets or code.',
    h1: 'Convert PDF Tables to CSV',
    intro: 'Use this page when CSV is the goal. Hisaab extracts the tables from your PDF, lets you correct them, and writes CSV files that open correctly in Excel and are safe from spreadsheet formula injection.',
    steps: ['Upload a PDF with tables.', 'Select and correct the tables.', 'Download a CSV (one table) or a ZIP of CSVs.'],
    details: [
      { h: 'CSV that behaves', p: 'Files use UTF-8 with a byte-order mark by default so Excel on Windows shows non-English characters correctly. Commas, quotes and line breaks inside cells are escaped properly.' },
      { h: 'Safe by default', p: 'Cells starting with =, +, - or @ get a leading apostrophe so a malicious PDF cannot make a spreadsheet run a formula when you open the file.' },
    ],
    limitations: ['CSV has no sheets, so several tables download as a ZIP.', 'Formatting such as colours and merged cells is not kept.'],
    faqs: [
      { q: 'Can I get CSV without the BOM?', a: 'The API supports it with bom=false. The web page uses the Excel-friendly default.' },
    ],
    related: ['pdf-table-extractor', 'bank-statement-to-excel'], guide: 'extract-tables-from-pdf',
  },
]

export const toolBySlug = (slug?: string) => TOOLS.find((t) => t.slug === slug)
export const toolPath = (slug: string) => `/tools/${slug}/`
