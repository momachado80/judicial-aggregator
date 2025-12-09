#!/usr/bin/env python3
"""
Mostra exemplos reais de como inventário/divórcio aparecem nos PDFs do DJE
"""
from pathlib import Path
import pdfplumber

PDF_DIR = Path("dje_pdfs")
encontrados = 0

print("Extraindo exemplos de publicacoes de inventario/divorcio...\n")

for pdf_path in sorted(PDF_DIR.glob("*.pdf"))[:50]:  # só os primeiros 50
    if encontrados >= 5:
        break
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                if encontrados >= 5:
                    break
                texto = page.extract_text() or ""
                texto_lower = texto.lower()
                
                # Procura menções a inventário ou divórcio
                for termo in ['inventário', 'divórcio']:
                    pos = texto_lower.find(termo)
                    if pos > 0:
                        # Pega 500 caracteres ao redor
                        inicio = max(0, pos - 200)
                        fim = min(len(texto), pos + 300)
                        trecho = texto[inicio:fim]
                        
                        print("=" * 70)
                        print(f"PDF: {pdf_path.name} | Termo: {termo}")
                        print("=" * 70)
                        print(trecho)
                        print("\n")
                        
                        encontrados += 1
                        break
    except:
        continue

print(f"\nExemplos extraidos: {encontrados}")
