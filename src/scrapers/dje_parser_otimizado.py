import pdfplumber
import re
from typing import List, Dict
from collections import defaultdict

def extrair_processos_dje_otimizado(pdf_path: str, max_paginas: int = None) -> List[Dict]:
    """Parser otimizado para PDFs grandes"""
    print(f"📄 Parseando: {pdf_path}")
    
    processos_dict = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        processar = min(max_paginas, total) if max_paginas else total
        
        print(f"📊 {total} páginas (processando {processar})")
        
        # Processar em blocos
        bloco = 50
        for inicio in range(0, processar, bloco):
            fim = min(inicio + bloco, processar)
            print(f"   Páginas {inicio+1}-{fim}...")
            
            # Juntar texto do bloco
            texto_bloco = ""
            for i in range(inicio, fim):
                texto_bloco += pdf.pages[i].extract_text() + "\n"
            
            # Buscar processos
            pattern = r'(\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4})'
            
            for match in re.finditer(pattern, texto_bloco):
                numero = match.group(1)
                
                if numero in processos_dict:
                    continue
                
                # Contexto
                start = max(0, match.start() - 1500)
                end = min(len(texto_bloco), match.end() + 1500)
                ctx = texto_bloco[start:end].lower()
                
                # Filtrar por tipo
                tipo = None
                if 'inventário' in ctx or 'arrolamento' in ctx:
                    tipo = 'Inventário'
                elif 'divórcio' in ctx:
                    tipo = 'Divórcio'
                elif 'alimentos' in ctx:
                    tipo = 'Alimentos'
                elif 'guarda' in ctx:
                    tipo = 'Guarda'
                
                if not tipo:
                    continue
                
                processos_dict[numero] = {
                    'numero': numero,
                    'tipo': tipo,
                    'codigo_comarca': numero.split('.')[-1]
                }
    
    processos = list(processos_dict.values())
    print(f"✅ {len(processos)} processos encontrados")
    return processos

if __name__ == "__main__":
    # Processar 200 páginas (amostra)
    pdf = "data/dje_pdfs/dje_14-11-2025_cad12.pdf"
    processos = extrair_processos_dje_otimizado(pdf, max_paginas=200)
    
    from collections import Counter
    
    print(f"\n📊 RESUMO (200 páginas):")
    tipos = Counter(p['tipo'] for p in processos)
    for tipo, count in tipos.items():
        print(f"   {tipo}: {count}")
    
    # Projeção
    print(f"\n🔮 PROJEÇÃO (1237 páginas completas):")
    fator = 1237 / 200
    for tipo, count in tipos.items():
        print(f"   {tipo}: ~{int(count * fator)}")
