import requests

url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
headers = {
    "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
}

# Processo que sabemos que TEM movimentações (testado antes)
numero = "00002337019898260361"

response = requests.post(url, json={"query": {"term": {"numeroProcesso": numero}}, "size": 1}, headers=headers)
data = response.json()

print("Status da resposta:", response.status_code)

if data.get("hits", {}).get("hits"):
    source = data["hits"]["hits"][0]["_source"]
    movs = source.get("movimentos", [])
    
    print(f"Total de movimentos: {len(movs)}")
    
    if movs:
        print(f"\nPrimeiros 3 movimentos:")
        for i, mov in enumerate(movs[:3], 1):
            print(f"\n{i}. Movimento:")
            print(f"   Codigo: {mov.get('codigo')}")
            print(f"   Nome: '{mov.get('nome')}'")
            print(f"   Data: {mov.get('dataHora')}")
    else:
        print("\nLista de movimentos vazia!")
else:
    print("Processo nao encontrado!")
    print("Resposta:", data)
