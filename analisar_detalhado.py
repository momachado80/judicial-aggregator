#!/usr/bin/env python3
"""
Analisa os PDFs que geraram detecção de imóveis
"""
import subprocess
import re
import json
from pathlib import Path

# Carregar processos que foram identificados com imóveis
with open("data/processos_com_imoveis.json", "r") as f:
    data = json.load(f)

processos = data.get("processos", [])[:10]
print(f"Analisando {len(processos)} processos identificados com imóveis...\n")

pasta = Path("data/dje_pdfs")
todos_pdfs = list(pasta.glob("*.pdf"))

KEYWORDS = ['imóvel', 'imovel', 'matrícula', 'matricula', 'escritura', 'itcmd', 'itbi', 'apartamento', 'terreno', 'casa', 'lote']

for proc in processos[:5]:
    numero = proc["numero"]
    numero_busca = numero.replace("-", "").replace(".", "")[:15]
    
    print(f"\n{'='*70}")
    print(f"Processo: {numero}")
    print(f"Tipo informado: {proc.get('tipo', '?')}")
    print(f"Comarca: {proc.get('comarca', proc.get('codigo_comarca', '?'))}")
    print('='*70)
    
    # Buscar em alguns PDFs
    encontrado = False
    for pdf in todos_pdfs[:500]:  # Limitar busca
        try:
            result = subprocess.run(['pdftotext', '-q', str(pdf), '-'], 
                                    capture_output=True, text=True, timeout=10)
            texto = result.stdout
            
            if numero in texto or numero_busca in texto:
                encontrado = True
                print(f"\n📄 Encontrado em: {pdf.name}")
                
                # Extrair contexto
                pos = texto.find(numero)
                if pos == -1:
                    pos = texto.find(numero_busca)
                
                if pos >= 0:
                    inicio = max(0, pos - 200)
                    fim = min(len(texto), pos + 800)
                    contexto = texto[inicio:fim]
                    
                    print(f"\n--- CONTEXTO ---")
                    print(contexto[:600])
                    print("--- FIM ---")
                    
                    # Verificar keywords de imóveis
                    keywords_encontradas = [kw for kw in KEYWORDS if kw in contexto.lower()]
                    if keywords_encontradas:
                        print(f"\n🏠 Keywords de imóvel: {keywords_encontradas}")
                    else:
                        print(f"\n⚠️ NENHUMA keyword de imóvel encontrada!")
                
                break
        except:
            continue
    
    if not encontrado:
        print("❌ Não encontrado nos PDFs analisados")

