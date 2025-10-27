import requests
import json

# URL e chave EXATAMENTE como no exemplo do GitHub
url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
api_key = "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJITzNjLV9TRENyQk1RdnFKZGRdw=="

payload = json.dumps({
    "size": 2,
    "query": {
        "match_all": {}
    }
})

headers = {
    'Authorization': api_key,
    'Content-Type': 'application/json'
}

print("🔍 Testando com setup EXATO do GitHub...")
print("="*60)

try:
    response = requests.request("POST", url, headers=headers, data=payload, timeout=30)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ FUNCIONOU!")
        print(f"Total: {data['hits']['total']['value']}")
        print(f"\nPrimeiro processo: {data['hits']['hits'][0]['_source']['numeroProcesso']}")
    else:
        print(f"\n❌ Erro: {response.text[:300]}")
        
except Exception as e:
    print(f"❌ Exceção: {e}")

print("="*60)
