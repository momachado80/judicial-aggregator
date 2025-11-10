"""
SCRAPER MASTER OTIMIZADO V2 - Com commits em lote
"""
import requests
import time
from src.database import get_db
from src.models import Processo
from sqlalchemy.exc import IntegrityError

PALAVRAS_FINALIZACAO = [
    "sentença extintiva", "sentenca extintiva",
    "processo extinto", "extinção", "extincao",
    "arquivamento", "arquivado definitivamente",
    "homologação da partilha", "homologacao da partilha",
    "partilha homologada", "trânsito em julgado", "transito em julgado",
    "baixa definitiva"
]

def processo_esta_ativo(movimentos):
    if not movimentos or len(movimentos) == 0:
        return True
    ultimas = movimentos[-15:] if len(movimentos) > 15 else movimentos
    texto = " ".join([m.get("nome", "").lower() for m in ultimas])
    return not any(palavra in texto for palavra in PALAVRAS_FINALIZACAO)

def coletar_tribunal(tribunal_sigla, api_url, max_processos=5000):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
    }
    
    db = next(get_db())
    tipos = ["Inventário", "Divórcio Litigioso", "Divórcio Consensual"]
    
    stats = {"encontrados": 0, "ativos": 0, "inativos": 0, "salvos": 0, "duplicados": 0}
    
    # BUFFER para commits em lote
    buffer_processos = []
    BATCH_SIZE = 50
    
    for tipo in tipos:
        print(f"\n📋 Buscando {tipo}...")
        from_page = 0
        sem_resultados = 0
        
        while from_page < max_processos and sem_resultados < 3:
            payload = {
                "query": {"match": {"classe.nome": tipo}},
                "size": 100,
                "from": from_page
            }
            
            try:
                response = requests.post(api_url, json=payload, headers=headers, timeout=30)
                data = response.json()
                hits = data.get("hits", {}).get("hits", [])
                
                if not hits:
                    sem_resultados += 1
                    from_page += 100
                    continue
                
                sem_resultados = 0
                
                for hit in hits:
                    source = hit.get("_source", {})
                    numero = source.get("numeroProcesso", "")
                    movimentos = source.get("movimentos", [])
                    
                    if not numero:
                        continue
                    
                    stats["encontrados"] += 1
                    
                    if not processo_esta_ativo(movimentos):
                        stats["inativos"] += 1
                        continue
                    
                    stats["ativos"] += 1
                    
                    # Verificar duplicado (sem commit)
                    existe = db.query(Processo).filter(
                        Processo.numero_processo == numero
                    ).first()
                    
                    if existe:
                        stats["duplicados"] += 1
                        continue
                    
                    numero_limpo = ''.join(c for c in numero if c.isdigit())
                    codigo_comarca = numero_limpo[-4:] if len(numero_limpo) >= 20 else "0000"
                    
                    processo = Processo(
                        numero_processo=numero,
                        tribunal=tribunal_sigla,
                        tipo_processo=tipo,
                        classe=tipo,
                        comarca=f"Comarca {codigo_comarca}",
                        relevancia="Alta",
                        score_relevancia=0.7,
                        status="pendente"
                    )
                    
                    buffer_processos.append(processo)
                    
                    # COMMIT EM LOTE
                    if len(buffer_processos) >= BATCH_SIZE:
                        try:
                            db.bulk_save_objects(buffer_processos)
                            db.commit()
                            stats["salvos"] += len(buffer_processos)
                            print(f"   ✅ {stats['salvos']} salvos | ❌ {stats['inativos']} inativos")
                            buffer_processos = []
                        except Exception as e:
                            db.rollback()
                            buffer_processos = []
                
                from_page += 100
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ⚠️  Erro: {str(e)[:60]}")
                time.sleep(2)
                continue
    
    # Salvar o que sobrou no buffer
    if buffer_processos:
        try:
            db.bulk_save_objects(buffer_processos)
            db.commit()
            stats["salvos"] += len(buffer_processos)
        except:
            db.rollback()
    
    return stats

print("="*70)
print("🚀 COLETA MASTER OTIMIZADA V2")
print("="*70)

print("\n📍 TJSP - Inventários e Divórcios ATIVOS")
stats_tjsp = coletar_tribunal("TJSP", "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search", 3000)

print("\n📍 TJBA - Inventários e Divórcios ATIVOS")
stats_tjba = coletar_tribunal("TJBA", "https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search", 3000)

print("\n" + "="*70)
print(f"💾 TJSP: {stats_tjsp['salvos']} salvos | 🗑️  {stats_tjsp['inativos']} inativos")
print(f"💾 TJBA: {stats_tjba['salvos']} salvos | 🗑️  {stats_tjba['inativos']} inativos")
print(f"🎯 TOTAL: {stats_tjsp['salvos'] + stats_tjba['salvos']} processos ATIVOS")
print("="*70)
