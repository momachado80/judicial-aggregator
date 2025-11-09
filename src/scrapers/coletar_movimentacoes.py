"""
Coleta movimentações de TODOS os processos que ainda não têm
"""
import requests
import time
from src.database import get_db
from src.models import Processo

url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
headers = {
    "Content-Type": "application/json",
    "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
}

print("🔍 COLETANDO MOVIMENTAÇÕES DE TODOS OS PROCESSOS")
print("="*60)

db = next(get_db())

# Pegar TODOS os processos sem movimentações
total_sem_mov = db.query(Processo).filter(
    Processo.movimentacoes == None,
    Processo.tribunal == "TJSP"
).count()

print(f"📊 Total de processos sem movimentações: {total_sem_mov:,}")
print(f"⏱️  Tempo estimado: ~{(total_sem_mov * 0.5) / 60:.0f} minutos")
print()

atualizados = 0
erros = 0
offset = 0
batch_size = 100

while True:
    processos_batch = db.query(Processo).filter(
        Processo.movimentacoes == None,
        Processo.tribunal == "TJSP"
    ).offset(offset).limit(batch_size).all()
    
    if not processos_batch:
        break
    
    print(f"📦 Processando lote {offset}-{offset+len(processos_batch)}...")
    
    for processo in processos_batch:
        numero = processo.numero_processo.replace("-", "").replace(".", "")
        
        payload = {
            "query": {"term": {"numeroProcesso": numero}},
            "size": 1
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            data = response.json()
            hits = data.get("hits", {}).get("hits", [])
            
            if hits:
                source = hits[0].get("_source", {})
                movimentos = source.get("movimentos", [])
                
                if movimentos:
                    import json
                    textos = [mov.get("movimento", {}).get("nome", "") 
                             for mov in movimentos[:50] if mov.get("movimento", {}).get("nome")]
                    
                    processo.movimentacoes = json.dumps(textos, ensure_ascii=False)
                    atualizados += 1
            
            db.commit()
            time.sleep(0.3)
            
        except Exception as e:
            erros += 1
            db.rollback()
            continue
    
    print(f"   ✅ {atualizados} atualizados | ❌ {erros} erros")
    offset += batch_size

print(f"\n{'='*60}")
print(f"🎉 CONCLUÍDO!")
print(f"✨ {atualizados:,} processos atualizados")
print(f"❌ {erros} erros")
print(f"{'='*60}")
