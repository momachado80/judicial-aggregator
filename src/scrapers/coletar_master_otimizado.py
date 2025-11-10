"""
SCRAPER MASTER OTIMIZADO
Coleta APENAS processos ATIVOS com potencial de imóveis
"""
import requests
import time
from src.database import get_db
from src.models import Processo
from sqlalchemy.exc import IntegrityError

# Palavras que indicam processo INATIVO
PALAVRAS_FINALIZACAO = [
    "sentença extintiva", "sentenca extintiva",
    "processo extinto", "extinção", "extincao",
    "arquivamento", "arquivado definitivamente",
    "homologação da partilha", "homologacao da partilha",
    "partilha homologada", "trânsito em julgado", "transito em julgado",
    "baixa definitiva"
]

def processo_esta_ativo(movimentos):
    """Verifica se processo está ativo"""
    if not movimentos or len(movimentos) == 0:
        return True  # Sem movimentações = assume ativo
    
    # Últimas 15 movimentações
    ultimas = movimentos[-15:] if len(movimentos) > 15 else movimentos
    texto = " ".join([m.get("nome", "").lower() for m in ultimas])
    
    return not any(palavra in texto for palavra in PALAVRAS_FINALIZACAO)

def coletar_tribunal(tribunal_sigla, api_url, max_processos=10000):
    """Coleta processos ativos de um tribunal"""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
    }
    
    db = next(get_db())
    
    # TIPOS DE PROCESSO COM MAIOR CHANCE DE IMÓVEIS
    tipos = ["Inventário", "Divórcio Litigioso", "Divórcio Consensual"]
    
    stats = {
        "encontrados": 0,
        "ativos": 0,
        "inativos": 0,
        "salvos": 0,
        "duplicados": 0
    }
    
    for tipo in tipos:
        print(f"\n📋 Buscando {tipo}...")
        from_page = 0
        sem_resultados = 0
        
        while from_page < max_processos and sem_resultados < 3:
            payload = {
                "query": {"match": {"classe.nome": tipo}},
                "size": 100,
                "from": from_page,
                "sort": [{"dataAjuizamento": {"order": "desc"}}]  # Mais recentes primeiro
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
                    
                    # FILTRO 1: Verificar se está ATIVO
                    if not processo_esta_ativo(movimentos):
                        stats["inativos"] += 1
                        continue
                    
                    stats["ativos"] += 1
                    
                    # Verificar se já existe
                    existe = db.query(Processo).filter(
                        Processo.numero_processo == numero
                    ).first()
                    
                    if existe:
                        stats["duplicados"] += 1
                        continue
                    
                    # Determinar comarca
                    numero_limpo = ''.join(c for c in numero if c.isdigit())
                    codigo_comarca = numero_limpo[-4:] if len(numero_limpo) >= 20 else "0000"
                    
                    # Calcular score
                    score = 0.5
                    if len(movimentos) > 10:
                        score += 0.2
                    
                    processo = Processo(
                        numero_processo=numero,
                        tribunal=tribunal_sigla,
                        tipo_processo=tipo,
                        classe=tipo,
                        comarca=f"Comarca {codigo_comarca}",
                        relevancia="Alta" if score >= 0.7 else "Média",
                        score_relevancia=score,
                        status="pendente"
                    )
                    
                    try:
                        db.add(processo)
                        db.commit()
                        stats["salvos"] += 1
                        
                        if stats["salvos"] % 50 == 0:
                            print(f"   ✅ {stats['salvos']} salvos | ❌ {stats['inativos']} inativos")
                        
                    except IntegrityError:
                        db.rollback()
                        stats["duplicados"] += 1
                
                from_page += 100
                time.sleep(0.3)
                
            except Exception as e:
                print(f"   ⚠️  Erro: {str(e)[:60]}")
                time.sleep(1)
                continue
    
    return stats

print("="*70)
print("🚀 COLETA MASTER OTIMIZADA - APENAS PROCESSOS ATIVOS")
print("="*70)

# TJSP
print("\n📍 TJSP - Tribunal de Justiça de São Paulo")
print("-"*70)
stats_tjsp = coletar_tribunal(
    "TJSP",
    "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search",
    max_processos=5000
)

# TJBA
print("\n📍 TJBA - Tribunal de Justiça da Bahia")
print("-"*70)
stats_tjba = coletar_tribunal(
    "TJBA",
    "https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search",
    max_processos=5000
)

# RESUMO FINAL
print("\n" + "="*70)
print("📊 RESUMO FINAL")
print("="*70)
print(f"\n🔵 TJSP:")
print(f"   Encontrados: {stats_tjsp['encontrados']}")
print(f"   ✅ Ativos: {stats_tjsp['ativos']}")
print(f"   ❌ Inativos (ignorados): {stats_tjsp['inativos']}")
print(f"   💾 Salvos: {stats_tjsp['salvos']}")
print(f"   🔄 Duplicados: {stats_tjsp['duplicados']}")

print(f"\n🟡 TJBA:")
print(f"   Encontrados: {stats_tjba['encontrados']}")
print(f"   ✅ Ativos: {stats_tjba['ativos']}")
print(f"   ❌ Inativos (ignorados): {stats_tjba['inativos']}")
print(f"   💾 Salvos: {stats_tjba['salvos']}")
print(f"   🔄 Duplicados: {stats_tjba['duplicados']}")

total_salvos = stats_tjsp['salvos'] + stats_tjba['salvos']
total_inativos = stats_tjsp['inativos'] + stats_tjba['inativos']

print(f"\n🎯 TOTAL:")
print(f"   💾 {total_salvos} processos ATIVOS salvos")
print(f"   🗑️  {total_inativos} processos INATIVOS ignorados")
print("="*70)
