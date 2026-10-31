# Third-party software

Hisaab's own code is MIT licensed. It depends on the packages below; check each project's license before redistributing a bundled build. Licenses listed are from memory of the upstream projects and **should be verified** against the versions you install (`pip-licenses`, `npx license-checker`).

| Package | Used for | License (verify) |
|---|---|---|
| FastAPI, Starlette, Uvicorn, Pydantic | API | MIT / BSD |
| pdfplumber, pdfminer.six | PDF text and tables | MIT |
| pypdfium2 (via pdfplumber) | PDF page rendering | Apache-2.0 / BSD-3 |
| Tesseract OCR, pytesseract | OCR | Apache-2.0 |
| OpenCV (headless), NumPy, Pillow | Image processing | Apache-2.0 / BSD / HPND |
| openpyxl | Excel files | MIT |
| React, React Router, Vite, Tailwind CSS, lucide-react | Frontend | MIT / ISC |

**PyMuPDF is deliberately not used.** It is AGPL-3.0 (or commercial) and would conflict with an MIT-licensed distribution. The PDF stack above is permissively licensed instead.
