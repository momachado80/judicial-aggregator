#!/usr/bin/env python3
from pathlib import Path
import pdfplumber
import re

PDF_DIR = Path("data/dje_pdfs")
encontrados = 0

# Termos que indicam imóveis
TERMOS_IMOVEL = ['imóvel', 'imovel', 'matrícula', 'matricula', 'registro de imóveis', 
                 'apartamento', 'terreno', 'lote', 'casa', 'fazenda', 'sítio', 'sitio',
                 'hectare', 'alqueire', 'm²', 'm2', 'metros quadrados']

print("Buscando mencoes a imoveis em inventarios/divorcios...\n")

for pdf_path in sorted(PDF_DIR.glob("*.pdf"))[:30]:
    if encontrados >= 8:
        break
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[10:100]:
                if encontrados >= 8:
                    break
                texto = page.extract_text() or ""
                texto_lower = texto.lower()
                
                # Primeiro verifica se tem inventario/divorcio
                if not any(t in texto_lower for t in ['inventário', 'divórcio', 'arrolamento']):
                    continue
                
                # Depois busca termos de imovel
                for termo in TERMOS_IMOVEL:
                    if termo in texto_lower:
                        pos = texto_lower.find(termo)
                        trecho = texto[max(0,pos-150):pos+350]
                        
                        print("=" * 70)
                        print(f"PDF: {pdf_path.name} | Pag: {page.page_number}")
                        print(f"Termo encontrado: {termo}")
                        print("=" * 70)
                        print(trecho)
                        print()
                        
                        encontrados += 1
                        break
    except:
        continue

print(f"\nMencoes a imoveis encontradas: {encontrados}")
if encontrados == 0:
    print("DJE nao contem detalhes sobre bens - apenas intimacoes de andamento.")
