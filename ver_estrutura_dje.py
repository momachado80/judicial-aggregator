#!/usr/bin/env python3
"""
Analisa onde aparecem as keywords de imóveis nos PDFs
"""
import subprocess
from pathlib import Path

KEYWORDS = ['matrícula', 'escritura', 'imóvel', 'itcmd']

pasta = Path("data/dje_pdfs")
pdfs = list(pasta.glob("*.pdf"))

print("Buscando menções a imóveis nos PDFs...\n")

encontrados = 0
for pdf in pdfs[:300]:
    try:
        result = subprocess.run(['pdftotext', '-q', str(pdf), '-'], 
                                capture_output=True, text=True, timeout=15)
        texto = result.stdout.lower()
        
        for kw in KEYWORDS:
            if kw in texto:
                # Encontrar contexto
                pos = texto.find(kw)
                contexto = texto[max(0,pos-300):pos+500]
                
                print(f"{'='*70}")
                print(f"PDF: {pdf.name}")
                print(f"Keyword: {kw}")
                print(f"{'='*70}")
                print(contexto)
                print("\n")
                
                encontrados += 1
                if encontrados >= 5:
                    break
        
        if encontrados >= 5:
            break
    except:
        continue

print(f"\nTotal de exemplos mostrados: {encontrados}")
