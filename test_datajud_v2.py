import requests
import json
import base64

# Várias tentativas de autenticação
TJSP_URL = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"

# Query simples
query = {
    "query": {
        "match_all": {}
    },
    "size": 1
}

print("🔍 Testando diferentes métodos de autenticação...\n")

# Teste 1: Sem autenticação (pública mesmo)
print("=" * 60)
print("TESTE 1: Sem autenticação")
print("=" * 60)
try:
    response = requests.post(TJSP_URL, json=query, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ FUNCIONA SEM AUTENTICAÇÃO!")
    else:
        print(f"Erro: {response.text[:200]}")
except Exception as e:
    print(f"Erro: {e}")

print("\n")

# Teste 2: Com a API Key do site
print("=" * 60)
print("TESTE 2: Com API Key do site")
print("=" * 60)
API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJITzNjLV9TRENyQk1RdnFKZGRdw=="
headers = {
    "Authorization": f"APIKey {API_KEY}",
    "Content-Type": "application/json"
}
try:
    response = requests.post(TJSP_URL, headers=headers, json=query, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ FUNCIONA COM API KEY!")
    else:
        print(f"Erro: {response.text[:200]}")
except Exception as e:
    print(f"Erro: {e}")

print("\n")

# Teste 3: Basic Auth
print("=" * 60)
print("TESTE 3: Basic Auth")
print("=" * 60)
try:
    response = requests.post(TJSP_URL, auth=('api', 'publica'), json=query, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ FUNCIONA COM BASIC AUTH!")
    else:
        print(f"Erro: {response.text[:200]}")
except Exception as e:
    print(f"Erro: {e}")

print("\n" + "=" * 60)
print("Conclusão: Nenhum método funcionou, precisamos da chave correta")
print("=" * 60)
