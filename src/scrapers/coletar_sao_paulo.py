"""
Coleta processos de SÃO PAULO usando os códigos corretos
"""
import requests
import time
from src.database import get_db
from src.models import Processo
from sqlalchemy.exc import IntegrityError

# Códigos de foro de São Paulo
CODIGOS_SAO_PAULO = {
    "0100": "São Paulo - Foro Central",
    "0577": "São Paulo - Foro Regional",
    "0506": "São Paulo - Foro Regional I",
    "0361": "São Paulo - Foro Regional II",
    "0362": "São Paulo - Foro Regional III",
    "0363": "São Paulo - Foro Regional IV",
    "0405": "São Paulo - Foro Regional V",
    "0404": "São Paulo - Foro Regional VI",
    "0549": "São Paulo - Foro Regional VII",
    "0548": "São Paulo - Foro Regional VIII",
    "0602": "São Paulo - Foro Regional IX",
}

url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
headers = {
    "Content-Type": "application/json",
    "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
}

print("🎯 COLETANDO PROCESSOS DE SÃO PAULO!")
print("="*60)

db = next(get_db())
total_novos = 0

for codigo, nome in CODIGOS_SAO_PAULO.items():
    print(f"\n📍 {nome} ({codigo})...")
    
    from_page = 0
    novos_foro = 0
    
    while from_page < 1000:
        payload = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"classe.nome": "Inventário"}},
                        {"wildcard": {"numeroProcesso": f"*826{codigo}*"}}
                    ]
                }
            },
            "size": 100,
            "from": from_page
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            data = response.json()
            hits = data.get("hits", {}).get("hits", [])
            
            if not hits:
                break
            
            for hit in hits:
                source = hit.get("_source", {})
                numero = source.get("numeroProcesso", "")
                
                if not numero:
                    continue
                
                existe = db.query(Processo).filter(
                    Processo.numero_processo == numero
                ).first()
                
                if existe:
                    continue
                
                processo = Processo(
                    numero_processo=numero,
                    tribunal="TJSP",
                    tipo_processo="Inventário",
                    classe="Inventário",
                    comarca="São Paulo",
                    relevancia="Alta",
                    score_relevancia=0.9,
                    status="pendente"
                )
                
                try:
                    db.add(processo)
                    db.commit()
                    novos_foro += 1
                    total_novos += 1
                except IntegrityError:
                    db.rollback()
            
            from_page += 100
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            break
    
    print(f"   ✅ {novos_foro} processos salvos")

print(f"\n{'='*60}")
print(f"🎉 TOTAL: {total_novos} processos de São Paulo!")
print(f"{'='*60}")
