"""
Coleta movimentações - VERSÃO CORRIGIDA
"""
import requests
import time
import sys
from src.database import get_db
from src.models import Processo

url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
headers = {
    "Content-Type": "application/json",
    "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
}

limite = int(sys.argv[1]) if len(sys.argv) > 1 else 20

print(f"🔍 Coletando movimentações de {limite} processos...")

db = next(get_db())

processos = db.query(Processo).filter(
    Processo.movimentacoes == None,
    Processo.tribunal == "TJSP"
).limit(limite).all()

print(f"📊 {len(processos)} processos encontrados\n")

atualizados = 0
sem_mov = 0

for i, processo in enumerate(processos, 1):
    numero = processo.numero_processo.replace("-", "").replace(".", "")
    
    try:
        response = requests.post(url, json={"query": {"term": {"numeroProcesso": numero}}, "size": 1}, headers=headers, timeout=30)
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        if hits:
            movimentos = hits[0].get("_source", {}).get("movimentos", [])
            
            if movimentos:
                import json
                # CORRIGIDO: pegar o campo 'nome' direto do objeto
                textos = []
                for mov in movimentos[:100]:  # Pegar até 100 movimentações
                    nome = mov.get("nome", "")
                    data_hora = mov.get("dataHora", "")
                    if nome:
                        textos.append(f"{data_hora[:10]} - {nome}")
                
                if textos:
                    processo.movimentacoes = json.dumps(textos, ensure_ascii=False)
                    db.commit()
                    atualizados += 1
                    print(f"✅ [{i}/{len(processos)}] {processo.numero_processo[-15:]}: {len(textos)} movimentações")
                else:
                    sem_mov += 1
                    print(f"⚠️  [{i}/{len(processos)}] {processo.numero_processo[-15:]}: movimentos sem texto")
            else:
                sem_mov += 1
                print(f"⚠️  [{i}/{len(processos)}] {processo.numero_processo[-15:]}: sem movimentações")
        
        time.sleep(0.5)
        
    except Exception as e:
        print(f"❌ [{i}/{len(processos)}] Erro: {str(e)[:60]}")
        db.rollback()

print(f"\n{'='*60}")
print(f"✅ {atualizados} processos atualizados")
print(f"⚠️  {sem_mov} processos sem movimentações")
print(f"{'='*60}")
