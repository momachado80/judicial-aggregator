#!/usr/bin/env python3
import os
import re
import json
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

KEYWORDS_IMOVEL = [
    'imóvel', 'imovel', 'matrícula', 'matricula', 'registro de imóveis',
    'escritura', 'itcmd', 'itbi', 'partilha de bens', 'bem imóvel',
    'apartamento', 'terreno', 'lote', 'fazenda', 'sítio', 'chácara'
]

PADRAO_PROCESSO = re.compile(r'\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4}')

def processar_pdf(caminho):
    try:
        result = subprocess.run(
            ['pdftotext', '-q', str(caminho), '-'],
            capture_output=True, text=True, timeout=30
        )
        texto = result.stdout.lower()
        
        numeros = set(PADRAO_PROCESSO.findall(result.stdout))
        processos = []
        
        for numero in numeros:
            pos = texto.find(numero.lower())
            contexto = texto[max(0,pos-300):pos+300] if pos >= 0 else texto[:600]
            
            eh_inventario = 'inventário' in contexto or 'inventario' in contexto or 'arrolamento' in contexto
            eh_divorcio = 'divórcio' in contexto or 'divorcio' in contexto
            
            if not (eh_inventario or eh_divorcio):
                continue
            
            tem_imovel = any(kw in contexto for kw in KEYWORDS_IMOVEL)
            
            processos.append({
                "numero": numero,
                "tipo": "Inventário" if eh_inventario else "Divórcio",
                "tem_imovel": tem_imovel,
                "codigo_comarca": numero[-4:] if len(numero) > 4 else None
            })
        
        return processos
    except Exception as e:
        return []

def main():
    pasta = Path("./data/dje_pdfs")
    if not pasta.exists():
        pasta = Path("./judicial-aggregator/data/dje_pdfs")
    
    pdfs = list(pasta.glob("*.pdf"))
    print(f"Total PDFs: {len(pdfs)}")
    
    todos = {}
    
    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(processar_pdf, pdf): pdf for pdf in pdfs}
        
        for i, future in enumerate(as_completed(futures)):
            if i % 200 == 0:
                print(f"Processados: {i}/{len(pdfs)}")
            
            for p in future.result():
                n = p["numero"]
                if n not in todos or p["tem_imovel"]:
                    todos[n] = p
    
    com_imovel = [p for p in todos.values() if p["tem_imovel"]]
    
    print(f"\n{'='*50}")
    print(f"Total processos: {len(todos)}")
    print(f"COM IMÓVEL: {len(com_imovel)}")
    print(f"{'='*50}")
    
    with open("data/processos_com_imoveis.json", "w") as f:
        json.dump({"total": len(todos), "com_imovel": len(com_imovel), "processos": list(todos.values())}, f, indent=2, ensure_ascii=False)
    
    print("\nExemplos COM IMÓVEL:")
    for p in com_imovel[:10]:
        print(f"  {p['numero']} ({p['tipo']})")

if __name__ == "__main__":
    main()
