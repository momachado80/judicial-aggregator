"""
Coleta processos e envia para API em produção
"""
import requests
import time

API_URL = "https://judicial-aggregator-production.up.railway.app"
DATAJUD_URL = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
}

print("🚀 Coletando processos de TODAS as comarcas de SP...")
print("📊 Conectando à API DataJud do CNJ...")

from_page = 0
total_enviados = 0
max_processos = 10000

while from_page < max_processos:
    payload = {
        "query": {"match": {"classe.nome": "Inventário"}},
        "size": 100,
        "from": from_page
    }
    
    try:
        # Buscar na API do CNJ
        response = requests.post(DATAJUD_URL, json=payload, headers=HEADERS, timeout=30)
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        if not hits:
            print(f"✅ Fim dos resultados em {from_page}")
            break
        
        print(f"📥 Processando {len(hits)} processos da página {from_page//100 + 1}...")
        
        # Enviar cada processo para a API
        for hit in hits:
            source = hit.get("_source", {})
            numero_cnj = source.get("numeroProcesso", "")
            
            if not numero_cnj:
                continue
            
            # Verificar se já existe
            check_url = f"{API_URL}/processes?numero_processo={numero_cnj}&page_size=1"
            check_resp = requests.get(check_url)
            
            if check_resp.json().get("total", 0) > 0:
                continue  # Já existe
            
            total_enviados += 1
        
        from_page += 100
        print(f"   ✅ Total coletado até agora: {total_enviados}")
        time.sleep(0.5)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        time.sleep(2)

print(f"\n🎉 CONCLUÍDO! {total_enviados} processos novos encontrados")
print("⚠️ Mas não consegui salvá-los pois não há endpoint POST /processes")
