import time
import pdfplumber
import pypdfium2 as pdfium

pdf_path = "data/dje_pdfs/dje_31-12-2024_cad14.pdf"

print(f"Testing with {pdf_path}")

# Test pdfplumber
start = time.time()
with pdfplumber.open(pdf_path) as pdf:
    # Extract first 10 pages only for test
    for i, page in enumerate(pdf.pages[:10]):
        text = page.extract_text()
end = time.time()
print(f"pdfplumber (10 pages): {end - start:.4f}s")

# Test pypdfium2
start = time.time()
pdf = pdfium.PdfDocument(pdf_path)
for i in range(10):
    page = pdf[i]
    textpage = page.get_textpage()
    text = textpage.get_text_range()
end = time.time()
print(f"pypdfium2 (10 pages): {end - start:.4f}s")
