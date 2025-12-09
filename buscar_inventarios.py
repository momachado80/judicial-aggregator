#!/usr/bin/env python3
from pathlib import Path
import pdfplumber

PDF_DIR = Path("data/dje_pdfs")
encontrados = 0

print("Buscando inventario/divorcio nos PDFs...\n")

for pdf_path in sorted(PDF_DIR.glob("*.pdf"))[:20]:
    if encontrados >= 5:
        break
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Amostra: paginas 10-20 (evita capa/indice)
            for page in pdf.pages[10:30]:
                if encontrados >= 5:
                    break
                texto = page.extract_text() or ""
                texto_lower = texto.lower()
                
                for termo in ['inventário', 'divórcio', 'arrolamento']:
                    if termo in texto_lower:
                        pos = texto_lower.find(termo)
                        trecho = texto[max(0,pos-100):pos+400]
                        
                        print("=" * 70)
                        print(f"PDF: {pdf_path.name} | Pag: {page.page_number} | Termo: {termo}")
                        print("=" * 70)
                        print(trecho)
                        print()
                        
                        encontrados += 1
                        break
    except Exception as e:
        continue

print(f"\nExemplos encontrados: {encontrados}")
