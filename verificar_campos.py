#!/usr/bin/env python3
"""
Verifica quais campos estão disponíveis no DataJud
"""
import json
import requests

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
headers = {"Content-Type": "application/json", "Authorization": f"APIKey {DATAJUD_API_KEY}"}

# Buscar alguns inventários
query = {
    "query": {"term": {"classe.codigo": 39}},
    "size": 5
}

response = requests.post(url, headers=headers, json=query, timeout=30)
data = response.json()
hits = data.get("hits", {}).get("hits", [])

print("Campos disponíveis em um processo de Inventário:\n")

if hits:
    source = hits[0].get("_source", {})
    for campo, valor in source.items():
        if isinstance(valor, (str, int, float, bool)) or valor is None:
            print(f"  {campo}: {valor}")
        elif isinstance(valor, list):
            print(f"  {campo}: [lista com {len(valor)} itens]")
        elif isinstance(valor, dict):
            print(f"  {campo}: {json.dumps(valor, ensure_ascii=False)[:100]}")
    
    print(f"\n\nValor da causa: {source.get('valorCausa', 'NÃO EXISTE')}")
    print(f"Valor: {source.get('valor', 'NÃO EXISTE')}")
