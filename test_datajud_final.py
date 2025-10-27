import requests
import json

# Chave do GitHub (completa)
API_KEY_FULL = "APIKey cDZHYzlZa0JadVREZDJCendQbXY2SkJITzNjLV9TRENyQk1RdnFKZGRdw=="

TJSP_URL = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"

headers = {
    "Authorization": API_KEY_FULL,
    "Content-Type": "application/json"
}

query = {
    "query": {
        "match_all": {}
    },
    "size": 2
}

print("🔍 Testando com a chave do GitHub...")
print("="*60)

try:
    response = requests.post(TJSP_URL, headers=headers, json=query, timeout=30)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n🎉 SUCESSO! API FUNCIONANDO!")
        print(f"Total de processos: {data.get('hits', {}).get('total', {}).get('value', 0)}")
        
        hits = data.get('hits', {}).get('hits', [])
        if hits:
            print("\n📄 PRIMEIRO PROCESSO:")
            processo = hits[0]['_source']
            print(f"Número: {processo.get('numeroProcesso')}")
            print(f"Tribunal: {processo.get('tribunal')}")
            print(f"Classe: {processo.get('classe', {}).get('nome')}")
    else:
        print(f"\n❌ Erro {response.status_code}")
        print(response.text[:500])
        
except Exception as e:
    print(f"❌ Erro: {e}")

print("="*60)
