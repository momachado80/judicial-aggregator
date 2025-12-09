#!/usr/bin/env python3
"""
Busca menções a valor da causa nos PDFs do DJE
"""
import subprocess
from pathlib import Path
import re

pasta = Path("data/dje_pdfs")
pdfs = list(pasta.glob("*.pdf"))

print("Buscando 'valor da causa' nos PDFs do DJE...\n")

PADROES = [
    r'valor da causa[:\s]*r?\$?\s*[\d.,]+',
    r'valor da ação[:\s]*r?\$?\s*[\d.,]+',
    r'valor atribuído[:\s]*r?\$?\s*[\d.,]+',
    r'r\$\s*[\d.,]+',
]

encontrados = 0
for pdf in pdfs[:200]:
    try:
        result = subprocess.run(['pdftotext', '-q', str(pdf), '-'], 
                                capture_output=True, text=True, timeout=15)
        texto = result.stdout.lower()
        
        # Buscar "valor da causa"
        if 'valor da causa' in texto or 'valor da ação' in texto:
            pos = texto.find('valor da causa')
            if pos == -1:
                pos = texto.find('valor da ação')
            
            contexto = texto[max(0,pos-100):pos+200]
            
            print(f"{'='*70}")
            print(f"PDF: {pdf.name}")
            print(f"{'='*70}")
            print(contexto)
            print("\n")
            
            encontrados += 1
            if encontrados >= 5:
                break
    except:
        continue

print(f"\nExemplos encontrados: {encontrados}")
