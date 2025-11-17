import pdfplumber
import re
from typing import List, Dict

def extrair_processos_dje(pdf_path: str, tipos: List[str] = ["Inventário", "Divórcio"]) -> List[Dict]:
    """Extrai processos do DJE"""
    print(f"📄 Parseando: {pdf_path}")
    processos = []
    processos_unicos = set()  # Para evitar duplicatas
    
    with pdfplumber.open(pdf_path) as pdf:
        total_paginas = len(pdf.pages)
        print(f"📊 {total_paginas} páginas")
        
        for i, page in enumerate(pdf.pages, 1):
            if i % 10 == 0:
                print(f"   Página {i}/{total_paginas}...")
            
            text = page.extract_text()
            if not text:
                continue
            
            # Regex para processo: NNNNNNN-DD.AAAA.8.26.OOOO
            pattern = r'(\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4})'
            
            for match in re.finditer(pattern, text):
                numero = match.group(1)
                
                # Evitar duplicatas
                if numero in processos_unicos:
                    continue
                
                # Contexto amplo
                start = max(0, match.start() - 1500)
                end = min(len(text), match.end() + 1500)
                contexto = text[start:end]
                
                # Verificar se menciona os tipos procurados
                tipo_encontrado = None
                for tipo in tipos:
                    if tipo.lower() in contexto.lower():
                        tipo_encontrado = tipo
                        break
                
                if not tipo_encontrado:
                    continue
                
                processos_unicos.add(numero)
                
                # Extrair informações
                codigo_comarca = numero.split('.')[-1]
                
                # Extrair classe do processo
                classe_match = re.search(r'(Apelação Cível|Inventário|Divórcio[^\n]*|Arrolamento)', contexto, re.IGNORECASE)
                classe = classe_match.group(1) if classe_match else tipo_encontrado
                
                # Extrair comarca (nome)
                comarca_match = re.search(r'Comarca de ([A-Z][a-zá-úÀ-Ú\s]+)', contexto, re.IGNORECASE)
                comarca = comarca_match.group(1).strip() if comarca_match else None
                
                # Se não achou comarca no texto, buscar antes do número
                if not comarca:
                    linha_processo = contexto[max(0, match.start() - 200):match.end() + 50]
                    comarca_match = re.search(r'-\s*([A-Z][a-zá-úÀ-Ú\s]+)\s*-', linha_processo)
                    comarca = comarca_match.group(1).strip() if comarca_match else f"Código {codigo_comarca}"
                
                # Extrair partes (Apelante/Apelado ou Requerente/Requerido)
                partes = []
                for parte_tipo in ['Apelante', 'Apelado', 'Requerente', 'Requerido', 'Autor', 'Réu']:
                    parte_match = re.search(f'{parte_tipo}:\s*([A-ZÀ-Ú][^-\n]+?)(?:\s*-|\n)', contexto)
                    if parte_match:
                        partes.append(f"{parte_tipo}: {parte_match.group(1).strip()}")
                
                # Extrair advogados
                advogados = []
                adv_matches = re.finditer(r'(OAB:\s*\d+/[A-Z]{2})', contexto)
                for adv_match in adv_matches:
                    # Pegar nome antes do OAB
                    pos = contexto.index(adv_match.group(1))
                    trecho = contexto[max(0, pos-100):pos]
                    nome_match = re.search(r'([A-Z][a-zá-úÀ-Ú\s]+(?:\s+[A-Z][a-zá-úÀ-Ú\s]+)*)\s*\(', trecho)
                    if nome_match:
                        advogados.append(f"{nome_match.group(1).strip()} ({adv_match.group(1)})")
                
                # Extrair valor
                valor_match = re.search(r'R\$\s*([\d.,]+)', contexto)
                valor = valor_match.group(1) if valor_match else None
                
                processos.append({
                    'numero': numero,
                    'tipo': tipo_encontrado,
                    'classe': classe,
                    'comarca': comarca,
                    'codigo_comarca': codigo_comarca,
                    'partes': partes,
                    'advogados': advogados,
                    'valor_causa': valor,
                    'pagina_dje': i
                })
    
    print(f"✅ {len(processos)} processos encontrados")
    return processos

if __name__ == "__main__":
    pdf_path = "data/dje_pdfs/dje_15-11-2025_cad11.pdf"
    processos = extrair_processos_dje(pdf_path)
    
    print(f"\n📋 RESUMO: {len(processos)} processos")
    
    from collections import Counter
    tipos_count = Counter(p['tipo'] for p in processos)
    for tipo, count in tipos_count.items():
        print(f"   {tipo}: {count}")
    
    print(f"\n🔍 DETALHES:")
    for p in processos:
        print(f"\n{'='*80}")
        print(f"Processo: {p['numero']}")
        print(f"Tipo: {p['tipo']}")
        print(f"Classe: {p['classe']}")
        print(f"Comarca: {p['comarca']} ({p['codigo_comarca']})")
        if p['partes']:
            print(f"Partes: {', '.join(p['partes'])}")
        if p['advogados']:
            print(f"Advogados: {', '.join(p['advogados'])}")
        if p['valor_causa']:
            print(f"Valor: R$ {p['valor_causa']}")
