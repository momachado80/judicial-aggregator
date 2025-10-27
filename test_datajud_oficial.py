import requests
import json

# CHAVE OFICIAL ATUAL DA WIKI
url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
api_key = "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

payload = json.dumps({
    "size": 5,
    "query": {
        "match_all": {}
    }
})

headers = {
    'Authorization': api_key,
    'Content-Type': 'application/json'
}

print("🔍 Testando com CHAVE OFICIAL ATUAL da Wiki CNJ...")
print("="*70)

try:
    response = requests.request("POST", url, headers=headers, data=payload, timeout=30)
    
    print(f"Status Code: {response.status_code}\n")
    
    if response.status_code == 200:
        data = response.json()
        print("✅✅✅ SUCESSO! API DATAJUD FUNCIONANDO! ✅✅✅\n")
        print(f"📊 Total de processos disponíveis: {data['hits']['total']['value']:,}")
        print(f"📄 Retornados nesta consulta: {len(data['hits']['hits'])}\n")
        
        print("="*70)
        print("EXEMPLOS DE PROCESSOS REAIS:")
        print("="*70)
        
        for i, hit in enumerate(data['hits']['hits'][:3], 1):
            processo = hit['_source']
            print(f"\n🔹 PROCESSO {i}:")
            print(f"   Número: {processo.get('numeroProcesso')}")
            print(f"   Tribunal: {processo.get('tribunal')}")
            print(f"   Classe: {processo.get('classe', {}).get('nome', 'N/A')}")
            print(f"   Órgão: {processo.get('orgaoJulgador', {}).get('nome', 'N/A')}")
            
        print("\n" + "="*70)
        print("🎉 PODEMOS BUSCAR DADOS REAIS DO TJSP E TJBA!")
        print("="*70)
    else:
        print(f"❌ Erro {response.status_code}")
        print(response.text[:500])
        
except Exception as e:
    print(f"❌ Exceção: {e}")

print("\n" + "="*70)
