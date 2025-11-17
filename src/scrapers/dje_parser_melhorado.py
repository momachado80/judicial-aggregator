import pdfplumber
import re
from typing import List, Dict

def extrair_todos_processos_dje(pdf_path: str) -> List[Dict]:
    """
    Extrai TODOS os processos do DJE, independente do tipo
    Depois filtramos por palavra-chave
    """
    print(f"📄 Parseando: {pdf_path}")
    processos_raw = []
    
    with pdfplumber.open(pdf_path) as pdf:
        texto_completo = ""
        for page in pdf.pages:
            texto_completo += page.extract_text() + "\n"
        
        # Regex para processo
        pattern = r'(\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4})'
        
        for match in re.finditer(pattern, texto_completo):
            numero = match.group(1)
            
            # Contexto AMPLO (2000 chars)
            start = max(0, match.start() - 2000)
            end = min(len(texto_completo), match.end() + 2000)
            contexto = texto_completo[start:end]
            
            processos_raw.append({
                'numero': numero,
                'contexto': contexto
            })
    
    print(f"   Encontrados {len(processos_raw)} processos (com duplicatas)")
    
    # Remover duplicatas
    processos_unicos = {}
    for p in processos_raw:
        if p['numero'] not in processos_unicos:
            processos_unicos[p['numero']] = p
    
    print(f"   {len(processos_unicos)} processos únicos")
    
    # Agora filtrar por palavras-chave
    palavras = ["inventário", "divórcio", "arrolamento", "partilha", "alimentos", "guarda"]
    processos_filtrados = []
    
    for numero, p in processos_unicos.items():
        contexto_lower = p['contexto'].lower()
        
        tipo_encontrado = None
        for palavra in palavras:
            if palavra in contexto_lower:
                tipo_encontrado = palavra.capitalize()
                break
        
        if not tipo_encontrado:
            continue
        
        # Extrair informações
        codigo_comarca = numero.split('.')[-1]
        
        # Extrair classe
        classe_match = re.search(r'(Apelação[^-\n]*|Inventário|Divórcio[^\n-]*|Arrolamento|Alimentos)', p['contexto'], re.IGNORECASE)
        classe = classe_match.group(1).strip() if classe_match else tipo_encontrado
        
        # Extrair comarca
        comarca_match = re.search(r'(?:Comarca de|de)\s+([A-ZÀ-Ú][a-zá-úÀ-Ú\s]+?)(?:\s*-|\n)', p['contexto'])
        comarca = comarca_match.group(1).strip() if comarca_match else f"Código {codigo_comarca}"
        
        # Extrair partes
        partes = []
        for parte_tipo in ['Apelante', 'Apelado', 'Requerente', 'Requerido', 'Autor', 'Réu']:
            parte_match = re.search(f'{parte_tipo}:\s*([^-\n]+?)(?:\s*-|\n)', p['contexto'])
            if parte_match:
                nome = parte_match.group(1).strip()
                if len(nome) < 100:  # Evitar pegar texto grande
                    partes.append(f"{parte_tipo}: {nome}")
        
        processos_filtrados.append({
            'numero': numero,
            'tipo': tipo_encontrado,
            'classe': classe,
            'comarca': comarca,
            'codigo_comarca': codigo_comarca,
            'partes': partes[:4],  # Max 4 partes
            'contexto_preview': p['contexto'][:200]
        })
    
    print(f"✅ {len(processos_filtrados)} processos de interesse")
    return processos_filtrados

if __name__ == "__main__":
    pdf_path = "data/dje_pdfs/dje_14-11-2025_cad11.pdf"
    processos = extrair_todos_processos_dje(pdf_path)
    
    from collections import Counter
    
    print(f"\n📊 RESUMO:")
    print(f"Total: {len(processos)}")
    
    tipos = Counter(p['tipo'] for p in processos)
    for tipo, count in tipos.items():
        print(f"   {tipo}: {count}")
    
    print(f"\n🔍 PROCESSOS ENCONTRADOS:")
    for p in processos[:10]:  # Mostrar 10 primeiros
        print(f"\n{'='*80}")
        print(f"Número: {p['numero']}")
        print(f"Tipo: {p['tipo']}")
        print(f"Classe: {p['classe']}")
        print(f"Comarca: {p['comarca']}")
        if p['partes']:
            print(f"Partes: {p['partes']}")
