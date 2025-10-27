import requests
import json

# Configuração
API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJITzNjLV9TRENyQk1RdnFKZGRdw=="
TJSP_URL = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"

headers = {
    "Authorization": f"APIKey {API_KEY}",
    "Content-Type": "application/json"
}

# Query simples - buscar 5 processos
query = {
    "query": {
        "match_all": {}
    },
    "size": 5
}

print("🔍 Testando API DataJud - TJSP...")
print(f"URL: {TJSP_URL}")
print(f"Query: {json.dumps(query, indent=2)}")
print("\n" + "="*50 + "\n")

try:
    response = requests.post(TJSP_URL, headers=headers, json=query, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print("\n" + "="*50 + "\n")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ SUCESSO! API está funcionando!")
        print(f"\nTotal de processos encontrados: {data.get('hits', {}).get('total', {}).get('value', 0)}")
        
        # Mostrar primeiro processo
        hits = data.get('hits', {}).get('hits', [])
        if hits:
            print("\n📄 PRIMEIRO PROCESSO:")
            primeiro = hits[0]['_source']
            print(json.dumps(primeiro, indent=2, ensure_ascii=False)[:1000])
            print("\n... (truncado)")
    else:
        print(f"❌ ERRO: {response.status_code}")
        print(f"Resposta: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ ERRO na requisição: {str(e)}")

print("\n" + "="*50)
