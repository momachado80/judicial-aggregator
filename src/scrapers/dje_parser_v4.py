"""
Parser DJE V4 - Captura dois formatos:
1) 1a instancia: CLASSE :INVENTARIO ... PROCESSO :numero
2) 2a instancia: Acao: Inventario; No origem: numero
"""
import re
from typing import List, Dict
import pypdfium2 as pdfium

CLASSES_INVENTARIO = ['inventário', 'inventario', 'arrolamento']
CLASSES_DIVORCIO = ['divórcio', 'divorcio']

def classificar_tipo(texto):
    texto = texto.lower()
    for c in CLASSES_INVENTARIO:
        if c in texto:
            return 'Inventário'
    for c in CLASSES_DIVORCIO:
        if c in texto:
            return 'Divórcio'
    return None

def extrair_processos_dje_v4(pdf_path: str) -> List[Dict]:
    processos = []
    vistos = set()
    
    try:
        pdf = pdfium.PdfDocument(pdf_path)
    except Exception as e:
        return []
    
    for page_num in range(len(pdf)):
        try:
            page = pdf[page_num]
            text = page.get_textpage().get_text_range()
        except:
            continue
        
        # FORMATO 1: 1a instancia - CLASSE :... PROCESSO :...
        pattern1 = r'CLASSE\s*:\s*([^\n]+)[\s\S]{0,500}?PROCESSO\s*:\s*(\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4})'
        for match in re.finditer(pattern1, text):
            classe = match.group(1).strip()
            numero = match.group(2).strip()
            tipo = classificar_tipo(classe)
            
            if tipo and numero not in vistos and not numero.endswith('.0000'):
                vistos.add(numero)
                processos.append({
                    'numero': numero,
                    'tipo': tipo,
                    'classe_original': classe,
                    'fonte': '1a_instancia',
                    'pagina': page_num + 1,
                })
        
        # FORMATO 2: 2a instancia - Acao: ...; No origem: ...
        pattern2 = r'Ação:\s*([^;]+);\s*Nº origem:\s*(\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4})'
        for match in re.finditer(pattern2, text):
            acao = match.group(1).strip()
            numero = match.group(2).strip()
            tipo = classificar_tipo(acao)
            
            if tipo and numero not in vistos and not numero.endswith('.0000'):
                vistos.add(numero)
                processos.append({
                    'numero': numero,
                    'tipo': tipo,
                    'classe_original': acao,
                    'fonte': '2a_instancia',
                    'pagina': page_num + 1,
                })
    
    return processos


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"Testando: {pdf_path}")
        procs = extrair_processos_dje_v4(pdf_path)
        print(f"Encontrados: {len(procs)} processos")
        for p in procs[:15]:
            print(f"  {p['numero']} - {p['tipo']} - {p['classe_original']} ({p['fonte']})")
