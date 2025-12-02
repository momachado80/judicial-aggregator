"""
Parser DJE V4 - Captura dois formatos:
1) 1a instância: PROCESSO :numero -> CLASSE :tipo (linhas consecutivas)
2) 2a instância: Ação: tipo; Nº origem: numero
"""
import re
from typing import List, Dict
import pypdfium2 as pdfium

CLASSES_VALIDAS = {
    'inventário': 'Inventário',
    'inventario': 'Inventário', 
    'arrolamento sumário': 'Inventário',
    'arrolamento sumario': 'Inventário',
    'arrolamento comum': 'Inventário',
    'divórcio consensual': 'Divórcio',
    'divorcio consensual': 'Divórcio',
    'divórcio litigioso': 'Divórcio',
    'divorcio litigioso': 'Divórcio',
}

def classificar_tipo(classe_texto):
    """Classifica apenas se a classe for EXATAMENTE uma das válidas"""
    classe_lower = classe_texto.lower().strip()
    
    for classe_valida, tipo in CLASSES_VALIDAS.items():
        if classe_lower == classe_valida or classe_lower.startswith(classe_valida):
            return tipo, classe_texto.strip()
    
    return None, None

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
        
        lines = text.split('\n')
        
        # FORMATO 1: 1a instância - PROCESSO na linha N, CLASSE na linha N+1
        for i in range(len(lines) - 1):
            line = lines[i].strip()
            
            # Procurar linha com PROCESSO :
            proc_match = re.search(r'PROCESSO\s*:\s*(\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4})', line, re.IGNORECASE)
            if proc_match:
                numero = proc_match.group(1)
                
                # Verificar CLASSE na próxima linha
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                classe_match = re.search(r'CLASSE\s*:\s*(.+)', next_line, re.IGNORECASE)
                
                if classe_match:
                    classe_texto = classe_match.group(1).strip()
                    tipo, classe_original = classificar_tipo(classe_texto)
                    
                    if tipo and numero not in vistos and not numero.endswith('.0000'):
                        vistos.add(numero)
                        processos.append({
                            'numero': numero,
                            'tipo': tipo,
                            'classe_original': classe_original,
                            'fonte': '1a_instancia',
                            'pagina': page_num + 1,
                        })
        
        # FORMATO 2: 2a instância - Ação: ...; Nº origem: ...
        pattern2 = r'Ação:\s*([^;]+);\s*Nº origem:\s*(\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4})'
        for match in re.finditer(pattern2, text):
            acao = match.group(1).strip()
            numero = match.group(2).strip()
            tipo, classe_original = classificar_tipo(acao)
            
            if tipo and numero not in vistos and not numero.endswith('.0000'):
                vistos.add(numero)
                processos.append({
                    'numero': numero,
                    'tipo': tipo,
                    'classe_original': classe_original,
                    'fonte': '2a_instancia',
                    'pagina': page_num + 1,
                })
    
    return processos


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"Testando: {pdf_path}")
        processos = extrair_processos_dje_v4(pdf_path)
        print(f"Encontrados: {len(processos)}")
        for p in processos[:10]:
            print(f"  {p['numero']} - {p['tipo']} - {p['classe_original']}")
