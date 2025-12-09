#!/usr/bin/env python3
"""
Valida processos com imóveis - versão corrigida
"""
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

# Classes válidas incluindo arrolamentos
CLASSES_VALIDAS_NOMES = [
    "inventário", "divórcio", "arrolamento"
]

COMARCAS = {
    "0344": "Marília", "0482": "Presidente Prudente", "0368": "Monte Alto",
    "0441": "Pereira Barreto", "0405": "Osasco", "0451": "Piracicaba",
    "0322": "Lins", "0356": "Mirandópolis", "0471": "Porto Feliz",
    "0362": "Mogi das Cruzes", "0268": "Itapecerica da Serra", 
    "0272": "Itapetininga", "0281": "Itapira", "0009": "Vila Prudente"
}

def classe_valida(nome_classe):
    """Verifica se a classe é inventário, divórcio ou arrolamento"""
    nome_lower = nome_classe.lower()
    return any(c in nome_lower for c in CLASSES_VALIDAS_NOMES)

def consultar_datajud(numero_processo):
    """Consulta DataJud para verificar classe do processo"""
    numero_limpo = numero_processo.replace("-", "").replace(".", "")
    
    url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"APIKey {DATAJUD_API_KEY}"
    }
    
    query = {
        "query": {"term": {"numeroProcesso": numero_limpo}},
        "size": 1
    }
    
    try:
        response = requests.post(url, headers=headers, json=query, timeout=15)
        if response.status_code != 200:
            return None
        
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        if not hits:
            return None
        
        source = hits[0].get("_source", {})
        classe = source.get("classe", {})
        nome_classe = classe.get("nome", "")
        
        return {
            "numero": numero_processo,
            "nome_classe": nome_classe,
            "valido": classe_valida(nome_classe)
        }
    except Exception as e:
        print(f"  Erro {numero_processo}: {e}")
        return None


def main():
    with open("data/processos_com_imoveis.json", "r") as f:
        data = json.load(f)
    
    processos = [p for p in data["processos"] if p.get("tem_imovel")]
    print(f"Total processos com imóvel para validar: {len(processos)}")
    
    validados = []
    invalidos = []
    nao_encontrados = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(consultar_datajud, p["numero"]): p for p in processos}
        
        for i, future in enumerate(as_completed(futures)):
            processo_original = futures[future]
            resultado = future.result()
            codigo = processo_original.get("codigo_comarca", "")
            
            processo_formatado = {
                "numero": processo_original["numero"],
                "tipo": processo_original.get("tipo", ""),
                "tem_imovel": True,
                "codigo_comarca": codigo,
                "comarca": COMARCAS.get(codigo, codigo),
                "url_tjsp": f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&dadosConsulta.valorConsultaNuUnificado={processo_original['numero']}"
            }
            
            if resultado:
                if resultado["valido"]:
                    processo_formatado["tipo"] = resultado["nome_classe"]
                    validados.append(processo_formatado)
                    print(f"  ✅ {processo_original['numero']} - {resultado['nome_classe']}")
                else:
                    invalidos.append({"numero": processo_original["numero"], "classe_real": resultado["nome_classe"]})
                    print(f"  ❌ {processo_original['numero']} - {resultado['nome_classe']}")
            else:
                # Não encontrado no DataJud - manter com tipo do PDF
                # Processos recentes podem não estar indexados ainda
                nao_encontrados.append(processo_formatado)
                print(f"  ⚠️ {processo_original['numero']} - Não no DataJud (mantendo)")
            
            if (i + 1) % 10 == 0:
                print(f"Processados: {i + 1}/{len(processos)}")
    
    # Incluir não encontrados (podem ser válidos, só não estão no DataJud ainda)
    todos_validos = validados + nao_encontrados
    
    print(f"\n{'='*60}")
    print(f"RESULTADO:")
    print(f"  Confirmados no DataJud: {len(validados)}")
    print(f"  Não encontrados (mantidos): {len(nao_encontrados)}")
    print(f"  Inválidos (removidos): {len(invalidos)}")
    print(f"  TOTAL FINAL: {len(todos_validos)}")
    print(f"{'='*60}")
    
    resultado = {"total": len(todos_validos), "processos": todos_validos}
    
    with open("data/processos_com_imoveis.json", "w") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    with open("src/data/processos_com_imoveis.json", "w") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    print(f"\nArquivo atualizado com {len(todos_validos)} processos!")
    
    if invalidos:
        print(f"\nRemovidos:")
        for inv in invalidos:
            print(f"  {inv['numero']} -> {inv['classe_real']}")

if __name__ == "__main__":
    main()
