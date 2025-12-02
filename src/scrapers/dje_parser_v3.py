"""
Parser DJE V3 - Deteccao precisa por estrutura CLASSE/PROCESSO
"""
import re
from typing import List, Dict
import pypdfium2 as pdfium

CLASSES_INVENTARIO = ['inventário', 'inventario', 'arrolamento']
CLASSES_DIVORCIO = ['divórcio', 'divorcio']

def extrair_processos_dje_v3(pdf_path: str) -> List[Dict]:
    processos = []
    
    try:
        pdf = pdfium.PdfDocument(pdf_path)
    except Exception as e:
        print(f"Erro ao abrir PDF {pdf_path}: {e}")
        return []
    
    for page_num in range(len(pdf)):
        try:
            page = pdf[page_num]
            text = page.get_textpage().get_text_range()
        except:
            continue
        
        # Buscar CLASSE seguido de PROCESSO
        pattern = r'CLASSE\s*:\s*([^\n]+)[\s\S]*?PROCESSO\s*:\s*(\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4})'
        
        for match in re.finditer(pattern, text):
            classe = match.group(1).strip().lower()
            numero = match.group(2).strip()
            
            # Verificar tipo
            tipo = None
            for c in CLASSES_INVENTARIO:
                if c in classe:
                    tipo = 'Inventário'
                    break
            if not tipo:
                for c in CLASSES_DIVORCIO:
                    if c in classe:
                        tipo = 'Divórcio'
                        break
            
            # So aceitar se for tipo valido e comarca valida (nao .0000)
            if tipo and not numero.endswith('.0000'):
                contexto = text[match.start():match.end()+500].lower()
                
                tem_imovel = any(p in contexto for p in [
                    'imóvel', 'imovel', 'apartamento', 'casa', 
                    'terreno', 'lote', 'matrícula', 'matricula'
                ])
                
                processos.append({
                    'numero': numero,
                    'tipo': tipo,
                    'classe_original': match.group(1).strip(),
                    'tem_imovel': tem_imovel,
                    'pagina': page_num + 1,
                })
    
    return processos


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"Testando: {pdf_path}")
        procs = extrair_processos_dje_v3(pdf_path)
        print(f"Encontrados: {len(procs)} processos")
        for p in procs[:10]:
            print(f"  {p['numero']} - {p['tipo']} - {p['classe_original']}")
