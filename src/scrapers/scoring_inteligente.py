"""
Score inteligente baseado em: tipo, comarca, valor, situação
"""
import json
from src.database import get_db
from src.models import Processo

print("🎯 CALCULANDO SCORE INTELIGENTE")
print("="*60)

db = next(get_db())

# Comarcas grandes (mais chance de imóveis valiosos)
COMARCAS_PREMIUM = ["São Paulo", "Campinas", "Guarulhos", "Santos", "Sorocaba", "Ribeirão Preto"]

processos = db.query(Processo).filter(
    Processo.tribunal == "TJSP",
    Processo.tipo_processo == "Inventário"
).all()

print(f"📊 Analisando {len(processos)} inventários...\n")

altissima = 0
alta = 0

for p in processos:
    score = 0.5  # Base
    
    # +0.3 se for comarca premium
    if p.comarca in COMARCAS_PREMIUM:
        score += 0.3
    
    # +0.2 se tiver movimentações
    if p.movimentacoes:
        try:
            movs = json.loads(p.movimentacoes)
            if len(movs) > 10:
                score += 0.2
                
                # +0.1 se tiver penhora/avaliação
                texto = " ".join(movs).lower()
                if any(x in texto for x in ["penhora", "avaliação", "avaliacao", "partilha", "arrolamento"]):
                    score += 0.1
        except:
            pass
    
    # Atualizar
    if score >= 0.95:
        p.relevancia = "Altíssima"
        altissima += 1
    elif score >= 0.8:
        p.relevancia = "Alta"
        alta += 1
    else:
        p.relevancia = "Média"
    
    p.score_relevancia = min(score, 1.0)
    
db.commit()

print(f"{'='*60}")
print(f"🔥 {altissima} processos com relevância ALTÍSSIMA")
print(f"⭐ {alta} processos com relevância ALTA")
print(f"{'='*60}")
