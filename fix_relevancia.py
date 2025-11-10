from src.database import get_db
from src.models import Processo

db = next(get_db())

# Padronizar todos os valores de relevância
processos = db.query(Processo).all()

for p in processos:
    if p.relevancia:
        # Remover acentos e converter para minúscula
        rel = p.relevancia.lower()
        if 'altíssima' in rel or 'altissima' in rel:
            p.relevancia = 'Alta'  # Vamos usar "Alta" mesmo para as altíssimas
        elif 'alta' in rel:
            p.relevancia = 'Alta'
        elif 'média' in rel or 'media' in rel:
            p.relevancia = 'Média'
        else:
            p.relevancia = 'Baixa'

db.commit()

# Contar
alta = db.query(Processo).filter(Processo.relevancia == 'Alta').count()
media = db.query(Processo).filter(Processo.relevancia == 'Média').count()
baixa = db.query(Processo).filter(Processo.relevancia == 'Baixa').count()

print(f"✅ Relevâncias padronizadas:")
print(f"   Alta: {alta}")
print(f"   Média: {media}")
print(f"   Baixa: {baixa}")
