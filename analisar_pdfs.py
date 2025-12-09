#!/usr/bin/env python3
"""
Analisa PDFs do DJE para entender estrutura e melhorar detecção de imóveis
"""
import subprocess
import re
import json

# Pegar um processo que foi identificado como tendo imóvel
with open("data/processos_com_imoveis.json", "r") as f:
    data = json.load(f)

# Buscar no PDF original qual texto gerou a detecção
KEYWORDS = ['imóvel', 'matrícula', 'escritura', 'itcmd', 'apartamento', 'terreno', 'casa']

def extrair_contexto_processo(pdf_path, numero_processo):
    """Extrai texto ao redor do número do processo"""
    result = subprocess.run(['pdftotext', '-q', pdf_path, '-'], capture_output=True, text=True, timeout=30)
    texto = result.stdout
    
    # Encontrar o processo
    pos = texto.find(numero_processo)
    if pos == -1:
        # Tentar sem formatação
        numero_limpo = numero_processo.replace("-", "").replace(".", "")
        pos = texto.lower().find(numero_limpo[:10])
    
    if pos >= 0:
        inicio = max(0, pos - 500)
        fim = min(len(texto), pos + 1000)
        return texto[inicio:fim]
    return None

# Analisar alguns PDFs recentes para ver estrutura
import os
from pathlib import Path

pasta = Path("data/dje_pdfs")
pdfs = sorted(pasta.glob("*.pdf"))[-10:]  # Últimos 10 PDFs

print("Analisando estrutura dos PDFs do DJE...\n")

# Extrair um trecho de cada PDF
for pdf in pdfs[:3]:
    print(f"\n{'='*60}")
    print(f"Arquivo: {pdf.name}")
    print('='*60)
    
    result = subprocess.run(['pdftotext', '-q', str(pdf), '-'], capture_output=True, text=True, timeout=30)
    texto = result.stdout[:5000]
    
    # Procurar padrões de inventário/divórcio
    inventarios = re.findall(r'Inventário[^.]{0,200}', texto, re.IGNORECASE)
    divorcios = re.findall(r'Divórcio[^.]{0,200}', texto, re.IGNORECASE)
    
    print(f"\nMenções a Inventário: {len(inventarios)}")
    if inventarios:
        print(f"  Exemplo: {inventarios[0][:150]}...")
    
    print(f"\nMenções a Divórcio: {len(divorcios)}")
    if divorcios:
        print(f"  Exemplo: {divorcios[0][:150]}...")
    
    # Procurar menções a imóveis
    for kw in KEYWORDS:
        matches = re.findall(rf'{kw}[^.]*\.', texto, re.IGNORECASE)
        if matches:
            print(f"\n  🏠 '{kw}' encontrado:")
            print(f"     {matches[0][:200]}")
            break

