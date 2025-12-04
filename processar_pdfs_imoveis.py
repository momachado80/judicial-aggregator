#!/usr/bin/env python3
"""
Processa PDFs do DJE para encontrar processos de Inventário/Divórcio COM IMÓVEIS
"""
import os
import re
import json
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("Instalando pdfplumber...")
    os.system("pip install pdfplumber")
    import pdfplumber

# Palavras-chave que indicam IMÓVEL
KEYWORDS_IMOVEL = [
    r'imóvel', r'imovel', r'imóveis', r'imoveis',
    r'matrícula\s*n?[º°]?\s*\d+', r'matricula\s*n?[º°]?\s*\d+',
    r'registro de imóveis', r'registro de imoveis',
    r'cartório de registro', r'cartorio de registro',
    r'escritura', r'escrituras',
    r'itcmd', r'itbi',
    r'partilha de bens',
    r'bem imóvel', r'bens imóveis',
    r'apartamento', r'casa', r'terreno', r'lote', r'fazenda', r'sítio', r'sitio', r'chácara', r'chacara',
    r'fração ideal', r'fracao ideal',
    r'condomínio', r'condominio',
]

# Padrão para encontrar números de processo
PADRAO_PROCESSO = re.compile(r'\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4}')

# Padrão para identificar classe do processo
PADRAO_INVENTARIO = re.compile(r'(inventário|inventario|arrolamento)', re.IGNORECASE)
PADRAO_DIVORCIO = re.compile(r'(divórcio|divorcio)', re.IGNORECASE)

def tem_imovel(texto):
    """Verifica se o texto menciona imóveis"""
    texto_lower = texto.lower()
    for kw in KEYWORDS_IMOVEL:
        if re.search(kw, texto_lower):
            return True
    return False

def extrair_comarca(numero_processo):
    """Extrai código da comarca do número do processo"""
    match = re.search(r'\.(\d{4})$', numero_processo)
    return match.group(1) if match else None

def processar_pdf(caminho_pdf):
    """Processa um PDF e retorna processos encontrados"""
    processos = []
    
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            texto_completo = ""
            for pagina in pdf.pages:
                texto = pagina.extract_text() or ""
                texto_completo += texto + "\n"
            
            # Encontrar todos os números de processo
            numeros = PADRAO_PROCESSO.findall(texto_completo)
            
            for numero in set(numeros):  # Usar set para evitar duplicados
                # Encontrar contexto ao redor do número (500 chars antes e depois)
                pos = texto_completo.find(numero)
                if pos == -1:
                    continue
                
                inicio = max(0, pos - 500)
                fim = min(len(texto_completo), pos + 500)
                contexto = texto_completo[inicio:fim]
                
                # Verificar se é inventário ou divórcio
                eh_inventario = bool(PADRAO_INVENTARIO.search(contexto))
                eh_divorcio = bool(PADRAO_DIVORCIO.search(contexto))
                
                if not (eh_inventario or eh_divorcio):
                    continue
                
                # Verificar se menciona imóvel
                menciona_imovel = tem_imovel(contexto)
                
                processos.append({
                    "numero": numero,
                    "tipo": "Inventário" if eh_inventario else "Divórcio",
                    "tem_imovel": menciona_imovel,
                    "codigo_comarca": extrair_comarca(numero),
                    "arquivo_pdf": os.path.basename(caminho_pdf),
                    "contexto": contexto[:200] if menciona_imovel else None
                })
    
    except Exception as e:
        print(f"  Erro em {caminho_pdf}: {e}")
    
    return processos

def main():
    pasta_pdfs = Path("./data/dje_pdfs") 
    if not pasta_pdfs.exists():
        pasta_pdfs = Path("./judicial-aggregator/data/dje_pdfs")
    
    print(f"Buscando PDFs em: {pasta_pdfs}")
    
    pdfs = list(pasta_pdfs.glob("*.pdf"))
    print(f"Total de PDFs: {len(pdfs)}")
    
    todos_processos = {}
    total_com_imovel = 0
    
    for i, pdf in enumerate(pdfs):
        if i % 100 == 0:
            print(f"Processando {i}/{len(pdfs)}...")
        
        processos = processar_pdf(pdf)
        
        for p in processos:
            numero = p["numero"]
            # Se já existe, atualizar se este tem imóvel
            if numero in todos_processos:
                if p["tem_imovel"]:
                    todos_processos[numero]["tem_imovel"] = True
                    todos_processos[numero]["contexto"] = p["contexto"]
            else:
                todos_processos[numero] = p
    
    # Estatísticas
    total = len(todos_processos)
    com_imovel = sum(1 for p in todos_processos.values() if p["tem_imovel"])
    inventarios = sum(1 for p in todos_processos.values() if p["tipo"] == "Inventário")
    divorcios = sum(1 for p in todos_processos.values() if p["tipo"] == "Divórcio")
    
    print(f"\n{'='*50}")
    print(f"RESULTADO:")
    print(f"  Total de processos únicos: {total}")
    print(f"  Inventários: {inventarios}")
    print(f"  Divórcios: {divorcios}")
    print(f"  COM IMÓVEL: {com_imovel}")
    print(f"{'='*50}")
    
    # Salvar resultado
    resultado = {
        "total": total,
        "com_imovel": com_imovel,
        "processos": list(todos_processos.values())
    }
    
    with open("data/processos_com_imoveis.json", "w") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    print(f"\nSalvo em: data/processos_com_imoveis.json")
    
    # Mostrar alguns com imóvel
    print(f"\nExemplos COM IMÓVEL:")
    count = 0
    for p in todos_processos.values():
        if p["tem_imovel"] and count < 5:
            print(f"  {p['numero']} ({p['tipo']}) - Comarca: {p['codigo_comarca']}")
            count += 1

if __name__ == "__main__":
    main()
