"""
Debug da API DataJud
"""
import requests

url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
headers = {
    "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==",
    "Content-Type": "application/json"
}

query = {
    "query": {"match": {"classe.nome": "Inventário"}},
    "size": 1
}

print("🔍 Testando API DataJud...")
print(f"URL: {url}")
print(f"Headers: {headers}")
print(f"Query: {query}\n")

try:
    response = requests.post(url, json=query, headers=headers, timeout=30)

    print(f"Status Code: {response.status_code}")
    print(f"Headers da resposta: {dict(response.headers)}")
    print(f"\nConteúdo bruto (primeiros 500 chars):")
    print(response.text[:500])
    print(f"\nTamanho da resposta: {len(response.text)} bytes")

    if response.status_code == 200:
        try:
            data = response.json()
            print("\n✅ JSON válido!")
            print(f"Total de resultados: {data.get('hits', {}).get('total', {}).get('value', 0)}")

            if data.get("hits", {}).get("hits"):
                import json
                processo = data["hits"]["hits"][0]["_source"]
                print("\n📋 Estrutura do primeiro processo:")
                print(json.dumps(processo, indent=2, ensure_ascii=False)[:2000])
        except Exception as e:
            print(f"\n❌ Erro ao processar JSON: {e}")
    else:
        print(f"\n❌ Erro HTTP: {response.status_code}")

except Exception as e:
    print(f"\n❌ Erro na requisição: {e}")
