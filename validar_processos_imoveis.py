#!/usr/bin/env python3
"""
Valida processos com imóveis consultando DataJud para confirmar classe
"""
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

CLASSES_VALIDAS = {
    39: "Inventário",
    12541: "Divórcio Litigioso", 
    12372: "Divórcio Consensual",
    1310: "Arrolamento Sumário",
    1311: "Arrolamento Comum"
}

COMARCAS = {
    "0344": "Marília", "0482": "Presidente Prudente", "0368": "Monte Alto",
    "0441": "Pereira Barreto", "0405": "Osasco", "0451": "Piracicaba",
    "0322": "Lins", "0356": "Mirandópolis", "0471": "Porto Feliz",
    "0362": "Mogi das Cruzes", "0268": "Itapecerica da Serra", 
    "0272": "Itapetininga", "0281": "Itapira", "0009": "Vila Prudente"
}

def consultar_datajud(numero_processo):
    """Consulta DataJud para verificar classe do processo"""
    # Remover formatação
    numero_limpo = numero_processo.replace("-", "").replace(".", "")
    
    url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"APIKey {DATAJUD_API_KEY}"
    }
    
    query = {
        "query": {
            "term": {"numeroProcesso": numero_limpo}
        },
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
        codigo_classe = classe.get("codigo")
        nome_classe = classe.get("nome", "")
        
        return {
            "numero": numero_processo,
            "codigo_classe": codigo_classe,
            "nome_classe": nome_classe,
            "valido": codigo_classe in CLASSES_VALIDAS,
            "assuntos": [a.get("nome") for a in source.get("assuntos", [])]
        }
    except Exception as e:
        print(f"  Erro {numero_processo}: {e}")
        return None


def main():
    # Carregar processos com imóveis
    with open("data/processos_com_imoveis.json", "r") as f:
        data = json.load(f)
    
    processos = [p for p in data["processos"] if p.get("tem_imovel")]
    print(f"Total processos com imóvel para validar: {len(processos)}")
    
    validados = []
    invalidos = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(consultar_datajud, p["numero"]): p 
            for p in processos
        }
        
        for i, future in enumerate(as_completed(futures)):
            processo_original = futures[future]
            resultado = future.result()
            
            if resultado:
                if resultado["valido"]:
                    codigo = processo_original.get("codigo_comarca", "")
                    validados.append({
                        "numero": processo_original["numero"],
                        "tipo": resultado["nome_classe"],
                        "tem_imovel": True,
                        "codigo_comarca": codigo,
                        "comarca": COMARCAS.get(codigo, codigo),
                        "url_tjsp": f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&dadosConsulta.valorConsultaNuUnificado={processo_original['numero']}"
                    })
                    print(f"  ✅ {processo_original['numero']} - {resultado['nome_classe']}")
                else:
                    invalidos.append({
                        "numero": processo_original["numero"],
                        "classe_real": resultado["nome_classe"]
                    })
                    print(f"  ❌ {processo_original['numero']} - {resultado['nome_classe']} (NÃO É INVENTÁRIO/DIVÓRCIO)")
            else:
                print(f"  ⚠️ {processo_original['numero']} - Não encontrado no DataJud")
            
            if (i + 1) % 10 == 0:
                print(f"Processados: {i + 1}/{len(processos)}")
    
    print(f"\n{'='*60}")
    print(f"RESULTADO:")
    print(f"  Válidos (Inventário/Divórcio): {len(validados)}")
    print(f"  Inválidos (outras classes): {len(invalidos)}")
    print(f"{'='*60}")
    
    # Salvar apenas os válidos
    resultado = {
        "total": len(validados),
        "processos": validados
    }
    
    with open("data/processos_com_imoveis.json", "w") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    # Copiar para src/data também
    with open("src/data/processos_com_imoveis.json", "w") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    print(f"\nArquivo atualizado com {len(validados)} processos válidos!")
    
    if invalidos:
        print(f"\nProcessos removidos (não são inventário/divórcio):")
        for inv in invalidos[:10]:
            print(f"  {inv['numero']} -> {inv['classe_real']}")

if __name__ == "__main__":
    main()
