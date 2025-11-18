"""
Teste para explorar a estrutura completa da API DataJud
e identificar quais campos podem ser usados para filtros precisos
"""
import requests
import json

url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
headers = {
    "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
}

print("="*80)
print("🔍 TESTE 1: Estrutura completa de um processo de Inventário")
print("="*80)

# Buscar 1 processo de Inventário para ver todos os campos disponíveis
query = {
    "query": {"match": {"classe.nome": "Inventário"}},
    "size": 1
}

response = requests.post(url, json=query, headers=headers, timeout=30)
data = response.json()

if data.get("hits", {}).get("hits"):
    processo = data["hits"]["hits"][0]["_source"]
    print("\n📋 CAMPOS DISPONÍVEIS:")
    print(json.dumps(processo, indent=2, ensure_ascii=False))

    print("\n" + "="*80)
    print("🔍 TESTE 2: Verificar se podemos filtrar por assunto")
    print("="*80)

    # Tentar filtrar por assunto específico (imóveis)
    query_assunto = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"classe.nome": "Inventário"}},
                    {"match": {"assunto": "imóvel"}}
                ]
            }
        },
        "size": 5
    }

    response2 = requests.post(url, json=query_assunto, headers=headers, timeout=30)
    data2 = response2.json()
    total_com_assunto = data2.get("hits", {}).get("total", {}).get("value", 0)

    print(f"\n✅ Total de processos de Inventário: {data.get('hits', {}).get('total', {}).get('value', 0)}")
    print(f"✅ Total com filtro 'assunto=imóvel': {total_com_assunto}")

    print("\n" + "="*80)
    print("🔍 TESTE 3: Verificar se podemos filtrar por comarca")
    print("="*80)

    # Tentar filtrar por comarca específica
    query_comarca = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"classe.nome": "Inventário"}},
                    {"match": {"orgaoJulgador.nomeOrgao": "São Paulo"}}
                ]
            }
        },
        "size": 5
    }

    response3 = requests.post(url, json=query_comarca, headers=headers, timeout=30)
    data3 = response3.json()
    total_sp = data3.get("hits", {}).get("total", {}).get("value", 0)

    print(f"\n✅ Total com filtro 'comarca=São Paulo': {total_sp}")

    if data3.get("hits", {}).get("hits"):
        print("\n📋 Exemplos encontrados:")
        for hit in data3["hits"]["hits"][:3]:
            src = hit["_source"]
            print(f"\n  - Processo: {src.get('numeroProcesso', 'N/A')}")
            print(f"    Órgão: {src.get('orgaoJulgador', {}).get('nomeOrgao', 'N/A')}")
            print(f"    Classe: {src.get('classe', {}).get('nome', 'N/A')}")
            print(f"    Assuntos: {src.get('assunto', 'N/A')}")

    print("\n" + "="*80)
    print("🔍 TESTE 4: Verificar se podemos filtrar por valor da causa")
    print("="*80)

    # Tentar filtrar por valor da causa
    query_valor = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"classe.nome": "Inventário"}}
                ],
                "filter": [
                    {"range": {"valorCausa": {"gte": 100000, "lte": 500000}}}
                ]
            }
        },
        "size": 5
    }

    response4 = requests.post(url, json=query_valor, headers=headers, timeout=30)
    data4 = response4.json()
    total_valor = data4.get("hits", {}).get("total", {}).get("value", 0)

    print(f"\n✅ Total com filtro 'valorCausa entre R$ 100k-500k': {total_valor}")

    print("\n" + "="*80)
    print("🔍 TESTE 5: Verificar filtro por código de classe")
    print("="*80)

    # Tentar filtrar por código de classe ao invés de nome
    query_codigo = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"classe.codigo": "39"}}  # Código correto para Inventário
                ]
            }
        },
        "size": 5
    }

    response5 = requests.post(url, json=query_codigo, headers=headers, timeout=30)
    data5 = response5.json()
    total_codigo = data5.get("hits", {}).get("total", {}).get("value", 0)

    print(f"\n✅ Total com filtro 'classe.codigo=39' (Inventário): {total_codigo}")

    if data5.get("hits", {}).get("hits"):
        print("\n📋 Exemplos com código 39:")
        for hit in data5["hits"]["hits"][:3]:
            src = hit["_source"]
            print(f"\n  - Processo: {src.get('numeroProcesso', 'N/A')}")
            print(f"    Classe código: {src.get('classe', {}).get('codigo', 'N/A')}")
            print(f"    Classe nome: {src.get('classe', {}).get('nome', 'N/A')}")

else:
    print("❌ Nenhum processo encontrado")
