from src.scrapers.dje_parser import extrair_processos_dje
from collections import Counter

# Pegar um PDF recente
pdf = 'data/dje_pdfs/dje_21-11-2025_cad12.pdf'

print('🧪 Testando parser SEM filtros...')
processos = extrair_processos_dje(
    pdf_path=pdf,
    tipos=['Inventário', 'Divórcio', 'Arrolamento'],
    filtrar_imoveis=False,
    filtrar_ativos=False,
    comarcas_filtro=None
)

print(f'\n✅ Total processos extraídos: {len(processos)}')

# Contar por tipo
tipos = Counter(p['tipo'] for p in processos)
print(f'\nPor tipo:')
for tipo, count in tipos.items():
    print(f'  {tipo}: {count}')
    
# Ver primeiros 3
print('\nPrimeiros 3 processos:')
for p in processos[:3]:
    print(f'  {p["numero"]} | {p["tipo"]} | Classe: {p["classe"]}')
