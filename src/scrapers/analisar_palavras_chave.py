"""
Analisa movimentações buscando palavras-chave que indicam IMÓVEIS
"""
import json
from src.database import get_db
from src.models import Processo

PALAVRAS_IMOVEIS = [
    "matrícula", "matricula", "imóvel", "imovel", "imóveis", "imoveis",
    "fração ideal", "fracao ideal", "transcrição", "transcricao",
    "registro de imóveis", "registro de imoveis", "averbação", "averbacao",
    "matrícula imobiliária", "matricula imobiliaria"
]

PALAVRAS_SITUACAO = [
    "penhora", "avaliação", "avaliacao", "leilão", "leilao",
    "hasta pública", "hasta publica", "adjudicação", "adjudicacao",
    "alienação judicial", "alienacao judicial", "partilha", "arrolamento"
]

print("🔍 ANALISANDO ÚLTIMOS 500 PROCESSOS COM MOVIMENTAÇÕES")
print("="*60)

db = next(get_db())

# Pegar os ÚLTIMOS processos com movimentações (ORDER BY id DESC)
processos = db.query(Processo).filter(
    Processo.movimentacoes != None,
    Processo.tribunal == "TJSP"
).order_by(Processo.id.desc()).limit(500).all()

print(f"📊 Analisando {len(processos)} processos...\n")

com_imoveis = 0
com_situacao_critica = 0
super_relevantes = 0

for processo in processos:
    try:
        movs = json.loads(processo.movimentacoes)
        
        if not movs or len(movs) == 0:
            continue
            
        texto_completo = " ".join(movs).lower()
        
        tem_imovel = any(palavra.lower() in texto_completo for palavra in PALAVRAS_IMOVEIS)
        tem_situacao = any(palavra.lower() in texto_completo for palavra in PALAVRAS_SITUACAO)
        
        if tem_imovel and tem_situacao:
            processo.score_relevancia = 1.0
            processo.relevancia = "Altíssima"
            super_relevantes += 1
            print(f"🔥 {processo.numero_processo[-15:]}: IMÓVEL + PENHORA/LEILÃO")
        elif tem_imovel:
            processo.score_relevancia = 0.9
            processo.relevancia = "Alta"
            com_imoveis += 1
            print(f"🏠 {processo.numero_processo[-15:]}: tem imóvel")
        elif tem_situacao:
            com_situacao_critica += 1
        
        db.commit()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        continue

print(f"\n{'='*60}")
print(f"🔥 {super_relevantes} processos SUPER RELEVANTES")
print(f"🏠 {com_imoveis} processos com imóveis")
print(f"⚖️  {com_situacao_critica} processos em situação crítica")
print(f"{'='*60}")
