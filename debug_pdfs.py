#!/usr/bin/env python3
from pathlib import Path
import pdfplumber

PDF_DIR = Path("data/dje_pdfs")

pdfs = list(PDF_DIR.glob("*.pdf"))[:5]
print(f"Total de PDFs encontrados: {len(list(PDF_DIR.glob('*.pdf')))}")
print()

for pdf_path in pdfs:
    print(f"=== {pdf_path.name} ===")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Paginas: {len(pdf.pages)}")
            if pdf.pages:
                texto = pdf.pages[0].extract_text() or ""
                print(f"Chars na pag 1: {len(texto)}")
                print(f"Primeiros 500 chars:")
                print(texto[:500])
    except Exception as e:
        print(f"ERRO: {e}")
    print()
