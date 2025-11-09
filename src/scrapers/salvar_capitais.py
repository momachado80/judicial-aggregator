"""
Salva processos das capitais no banco via API
"""
import requests
import time

COMARCAS_PRIORITARIAS = {
    "TJSP": {
        "0538": "Santo André",
        "0584": "Sorocaba", 
        "0491": "Ribeirão Preto",
        "0068": "Bauru"
    },
    "TJBA": {
        "0001": "Salvador",
        "0005": "Feira de Santana"
    }
}

def buscar_e_salvar(tribunal, codigo, nome_comarca):
    """Busca e salva processos de uma comarca"""
    
    if tribunal == "TJSP":
        url_api = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
    else:
        url_api = "https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
    }
    
    print(f"\n🔍 {nome_comarca} ({codigo})...")
    
    novos = 0
    from_page = 0
    
    while from_page < 1000:  # Máximo 1000 por comarca
        payload = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"classe.nome": "Inventário"}},
                        {"wildcard": {"numeroProcesso": f"*{codigo}"}}
                    ]
                }
            },
            "size": 100,
            "from": from_page
        }
        
        try:
            response = requests.post(url_api, json=payload, headers=headers, timeout=30)
            data = response.json()
            hits = data.get("hits", {}).get("hits", [])
            
            if not hits:
                break
            
            # Enviar para backend
            processos_batch = []
            for hit in hits:
                source = hit.get("_source", {})
                numero = source.get("numeroProcesso", "")
                if numero:
                    processos_batch.append({
                        "numero_cnj": numero,
                        "tribunal": tribunal,
                        "comarca": nome_comarca,
                        "tipo_processo": "Inventário",
                        "classe": "Inventário"
                    })
            
            # Salvar via endpoint (que precisamos criar)
            print(f"   📥 {len(processos_batch)} processos nesta página")
            novos += len(processos_batch)
            
            from_page += 100
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            break
    
    print(f"   ✅ Total: {novos} processos")
    return novos

print("="*60)
print("💾 SALVANDO PROCESSOS DAS GRANDES CIDADES")
print("="*60)

total_geral = 0

for tribunal, comarcas in COMARCAS_PRIORITARIAS.items():
    for codigo, nome in comarcas.items():
        total = buscar_e_salvar(tribunal, codigo, nome)
        total_geral += total

print(f"\n{'='*60}")
print(f"🎉 CONCLUÍDO!")
print(f"📊 Total coletado: {total_geral} processos")
print(f"{'='*60}")
print("\n⚠️ IMPORTANTE: Esses processos foram coletados mas")
print("   precisam ser salvos no banco via endpoint POST")
