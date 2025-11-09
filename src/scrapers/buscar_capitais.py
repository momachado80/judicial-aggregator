"""
Busca processos especificamente das capitais e grandes cidades
"""
import requests
import time
from src.database import get_db
from src.models import Processo
from src.utils.comarcas_data import COMARCAS_TJSP, COMARCAS_TJBA

# Principais comarcas que DEVEM ter processos
COMARCAS_PRIORITARIAS = {
    "TJSP": {
        "0026": "São Paulo",      # Capital
        "0109": "Campinas",        # 2ª maior
        "0216": "Guarulhos",       # 3ª maior  
        "0548": "São Bernardo",    # ABC
        "0538": "Santo André",     # ABC
        "0561": "São José Campos", # Vale
        "0584": "Sorocaba",        # Interior
        "0491": "Ribeirão Preto",  # Interior
        "0068": "Bauru",           # Interior
        "0437": "Piracicaba"       # Interior
    },
    "TJBA": {
        "0001": "Salvador",        # Capital
        "0005": "Feira Santana",   # 2ª maior
        "0429": "Vitória Conquista" # 3ª maior
    }
}

def buscar_por_comarca_codigo(tribunal: str, codigo: str, nome_comarca: str):
    """Busca processos por código específico de comarca"""
    
    if tribunal == "TJSP":
        url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
    else:
        url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
    }
    
    print(f"\n🔍 Buscando {nome_comarca} ({codigo})...")
    
    # Buscar processos que TERMINAM com esse código
    payload = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"classe.nome": "Inventário"}},
                    {"wildcard": {"numeroProcesso": f"*{codigo}"}}
                ]
            }
        },
        "size": 100
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        data = response.json()
        
        total = data.get("hits", {}).get("total", {}).get("value", 0)
        hits = data.get("hits", {}).get("hits", [])
        
        print(f"   📊 Total encontrado: {total}")
        print(f"   📥 Retornados: {len(hits)}")
        
        if len(hits) > 0:
            print(f"   ✅ SUCESSO! Encontrou processos de {nome_comarca}")
            print(f"   Exemplo: {hits[0].get('_source', {}).get('numeroProcesso', '')}")
            return hits
        else:
            print(f"   ⚠️ Nenhum processo encontrado")
            return []
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return []

def main():
    print("="*60)
    print("🎯 BUSCA DIRECIONADA - CAPITAIS E GRANDES CIDADES")
    print("="*60)
    
    todos_processos = []
    
    for tribunal, comarcas in COMARCAS_PRIORITARIAS.items():
        print(f"\n{'='*60}")
        print(f"🏛️ {tribunal}")
        print(f"{'='*60}")
        
        for codigo, nome in comarcas.items():
            processos = buscar_por_comarca_codigo(tribunal, codigo, nome)
            todos_processos.extend(processos)
            time.sleep(1)  # Rate limiting
    
    print(f"\n{'='*60}")
    print(f"📊 RESUMO FINAL")
    print(f"{'='*60}")
    print(f"Total de processos encontrados: {len(todos_processos)}")
    
    if len(todos_processos) > 0:
        print("\n✅ ÓTIMA NOTÍCIA! A API tem processos das grandes cidades!")
        print("Agora precisamos salvar esses processos no banco.")
    else:
        print("\n⚠️ A API do CNJ pode estar:")
        print("  - Bloqueando buscas por comarca específica")
        print("  - Sem processos públicos de grandes cidades")
        print("  - Exigindo autenticação diferente")

if __name__ == "__main__":
    main()
