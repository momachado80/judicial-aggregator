"""
Salva os processos coletados no banco de produção
"""
import requests
import time
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath('.'))

from src.database import get_db
from src.models import Processo
from sqlalchemy.exc import IntegrityError

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

def buscar_e_salvar_no_banco(tribunal, codigo, nome_comarca, db):
    """Busca API e salva direto no banco"""
    
    if tribunal == "TJSP":
        url_api = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
    else:
        url_api = "https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
    }
    
    print(f"\n💾 {nome_comarca} ({codigo})...")
    
    novos = 0
    duplicados = 0
    from_page = 0
    
    while from_page < 1000:
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
            
            # Salvar cada processo
            for hit in hits:
                source = hit.get("_source", {})
                numero = source.get("numeroProcesso", "")
                
                if not numero:
                    continue
                
                # Verificar se já existe
                existe = db.query(Processo).filter(
                    Processo.numero_processo == numero
                ).first()
                
                if existe:
                    duplicados += 1
                    continue
                
                # Criar processo
                processo = Processo(
                    numero_processo=numero,
                    tribunal=tribunal,
                    tipo_processo="Inventário",
                    classe="Inventário",
                    comarca=nome_comarca,
                    relevancia="Alta",
                    score_relevancia=0.8,
                    status="pendente"
                )
                
                try:
                    db.add(processo)
                    db.commit()
                    novos += 1
                except IntegrityError:
                    db.rollback()
                    duplicados += 1
            
            print(f"   📥 Página {from_page//100 + 1}: +{novos} novos, ~{duplicados} duplicados")
            
            from_page += 100
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            db.rollback()
            break
    
    print(f"   ✅ Total salvos: {novos} processos")
    return novos

print("="*60)
print("💾 SALVANDO NO BANCO DE PRODUÇÃO")
print("="*60)

db = next(get_db())
total_geral = 0

for tribunal, comarcas in COMARCAS_PRIORITARIAS.items():
    for codigo, nome in comarcas.items():
        total = buscar_e_salvar_no_banco(tribunal, codigo, nome, db)
        total_geral += total

print(f"\n{'='*60}")
print(f"🎉 CONCLUÍDO!")
print(f"✨ Total salvos no banco: {total_geral} processos")
print(f"{'='*60}")
