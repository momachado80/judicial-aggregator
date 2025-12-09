#!/usr/bin/env python3
"""
Parser preciso - identifica blocos de processo individualmente
"""
import subprocess
import re
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

KEYWORDS_IMOVEL = [
    'imóvel', 'imovel', 'matrícula', 'matricula', 'escritura',
    'itcmd', 'itbi', 'partilha de bens', 'bem imóvel',
    'apartamento', 'terreno', 'lote', 'fazenda', 'sítio', 'chácara'
]

CLASSES_VALIDAS = [
    'inventário', 'inventario', 'arrolamento', 
    'divórcio', 'divorcio'
]

# Padrão para encontrar número CNJ
PADRAO_PROCESSO = re.compile(r'(\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4})')

# Padrão para encontrar classe
PADRAO_CLASSE = re.compile(r'CLASSE\s*:?\s*([A-ZÀ-Ú][A-Za-zÀ-ú\s]+)', re.IGNORECASE)

def extrair_blocos_processo(texto):
    """
    Divide o texto em blocos, um para cada processo.
    Cada bloco vai do número do processo até o próximo número.
    """
    matches = list(PADRAO_PROCESSO.finditer(texto))
    blocos = []
    
    for i, match in enumerate(matches):
        inicio = match.start()
        fim = matches[i + 1].start() if i + 1 < len(matches) else min(inicio + 2000, len(texto))
        
        bloco = texto[inicio:fim]
        numero = match.group(1)
        
        blocos.append({
            "numero": numero,
            "texto": bloco
        })
    
    return blocos

def processar_pdf(caminho):
    try:
        result = subprocess.run(
            ['pdftotext', '-q', str(caminho), '-'],
            capture_output=True, text=True, timeout=30
        )
        texto = result.stdout
        
        blocos = extrair_blocos_processo(texto)
        processos = []
        
        for bloco in blocos:
            numero = bloco["numero"]
            texto_bloco = bloco["texto"].lower()
            
            # Verificar se a CLASSE é válida (inventário/divórcio)
            classe_match = PADRAO_CLASSE.search(bloco["texto"])
            if classe_match:
                classe = classe_match.group(1).strip().lower()
            else:
                classe = ""
            
            eh_valido = any(c in classe for c in CLASSES_VALIDAS)
            
            if not eh_valido:
                continue
            
            # Verificar se tem keyword de imóvel NO MESMO BLOCO
            tem_imovel = any(kw in texto_bloco for kw in KEYWORDS_IMOVEL)
            
            if tem_imovel:
                tipo = "Inventário" if "inventário" in classe or "arrolamento" in classe else "Divórcio"
                processos.append({
                    "numero": numero,
                    "tipo": tipo,
                    "classe_original": classe_match.group(1).strip() if classe_match else "",
                    "tem_imovel": True,
                    "codigo_comarca": numero[-4:],
                    "arquivo_pdf": caminho.name
                })
        
        return processos
    except Exception as e:
        return []

def main():
    pasta = Path("data/dje_pdfs")
    pdfs = list(pasta.glob("*.pdf"))
    print(f"Total PDFs: {len(pdfs)}")
    
    todos = {}
    
    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(processar_pdf, pdf): pdf for pdf in pdfs}
        
        for i, future in enumerate(as_completed(futures)):
            if i % 200 == 0:
                print(f"Processados: {i}/{len(pdfs)} | Encontrados: {len(todos)}")
            
            for p in future.result():
                n = p["numero"]
                if n not in todos:
                    todos[n] = p
    
    # Adicionar URL e comarca nome
    COMARCAS = {
        "0344": "Marília", "0482": "Presidente Prudente", "0368": "Monte Alto",
        "0441": "Pereira Barreto", "0405": "Osasco", "0451": "Piracicaba",
        "0322": "Lins", "0356": "Mirandópolis", "0471": "Porto Feliz",
        "0362": "Mogi das Cruzes", "0268": "Itapecerica da Serra", 
        "0272": "Itapetininga", "0281": "Itapira", "0009": "Vila Prudente",
        "0100": "São Paulo", "0001": "Santana", "0002": "Santo Amaro",
        "0114": "Campinas", "0577": "São José dos Campos", "0554": "Ribeirão Preto"
    }
    
    for p in todos.values():
        codigo = p["codigo_comarca"]
        p["comarca"] = COMARCAS.get(codigo, codigo)
        p["url_tjsp"] = f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&dadosConsulta.valorConsultaNuUnificado={p['numero']}"
    
    lista = list(todos.values())
    
    print(f"\n{'='*50}")
    print(f"RESULTADO FINAL:")
    print(f"  Processos de Inventário/Divórcio COM IMÓVEL: {len(lista)}")
    print(f"{'='*50}")
    
    # Estatísticas
    inventarios = sum(1 for p in lista if "Inventário" in p["tipo"])
    divorcios = sum(1 for p in lista if "Divórcio" in p["tipo"])
    print(f"  Inventários: {inventarios}")
    print(f"  Divórcios: {divorcios}")
    
    # Salvar
    resultado = {"total": len(lista), "processos": lista}
    with open("data/processos_com_imoveis.json", "w") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    with open("src/data/processos_com_imoveis.json", "w") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    print(f"\nExemplos:")
    for p in lista[:10]:
        print(f"  {p['numero']} | {p['classe_original']} | {p['comarca']}")

if __name__ == "__main__":
    main()
