"""
Parser DJE v2 - Versão mais flexível que captura mais processos
"""
import re
from typing import List, Dict, Optional

# Palavras-chave que indicam IMÓVEIS
PALAVRAS_IMOVEIS = [
    "imóvel", "imovel", "terreno", "casa", "apartamento", "apto",
    "propriedade", "lote", "chácara", "chacara", "sítio", "sitio",
    "fazenda", "condomínio", "condominio", "edifício", "edificio",
    "residência", "residencia", "comercial", "sala comercial",
    "galpão", "galpao", "armazém", "armazem", "loja",
    "registro de imóveis", "registro de imoveis", "matricula", "matrícula",
    "escritura", "metragem", "m²", "m2", "área construída", "area construida",
    "unidade autônoma", "unidade autonoma", "área privativa", "area privativa",
    "endereço", "endereco", "rua ", "avenida", "av.", "praça", "praca"
]

# Palavras que indicam processo EXTINTO
PALAVRAS_EXTINTO = [
    "extinto", "arquivado", "baixado", "sentença de extinção",
    "sentenca de extincao", "processo extinto", "arquivamento"
]

def tem_imovel(texto: str) -> bool:
    texto_lower = texto.lower()
    return any(palavra.lower() in texto_lower for palavra in PALAVRAS_IMOVEIS)

def esta_ativo(texto: str) -> bool:
    texto_lower = texto.lower()
    return not any(palavra.lower() in texto_lower for palavra in PALAVRAS_EXTINTO)

def calcular_relevancia(texto: str) -> tuple:
    texto_lower = texto.lower()
    tem_imovel_flag = tem_imovel(texto)
    tem_urgencia = any(p in texto_lower for p in ["penhora", "leilão", "leilao", "hasta", "partilha"])
    
    if tem_imovel_flag and tem_urgencia:
        return ("Altíssima", 1.0)
    elif tem_imovel_flag:
        return ("Alta", 0.8)
    elif tem_urgencia:
        return ("Média", 0.5)
    return ("Baixa", 0.2)

def extrair_processos_dje_v2(
    pdf_path: str,
    tipos: List[str] = ["Inventário", "Divórcio", "Arrolamento"],
    filtrar_imoveis: bool = False,
    filtrar_ativos: bool = False,
    comarcas_filtro: Optional[List[str]] = None,
    verbose: bool = True
) -> List[Dict]:
    """
    Parser V2 - Mais flexível, captura processos por PALAVRA-CHAVE no contexto
    Não exige encontrar CLASSE em formato específico
    """
    if verbose:
        print(f"📄 [V2] Parseando: {pdf_path}")

    import pypdfium2 as pdfium

    processos = []
    processos_unicos = set()
    
    try:
        pdf = pdfium.PdfDocument(pdf_path)
        total_paginas = len(pdf)
        
        if verbose:
            print(f"📊 {total_paginas} páginas")

        for i in range(total_paginas):
            if verbose and (i + 1) % 200 == 0:
                print(f"   Página {i + 1}/{total_paginas}...")
            
            page = pdf[i]
            textpage = page.get_textpage()
            text = textpage.get_text_range()
            
            if not text:
                continue
            
            # Regex para processo TJSP: NNNNNNN-DD.AAAA.8.26.OOOO
            pattern = r'(\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4})'
            
            for match in re.finditer(pattern, text):
                numero = match.group(1)

                if numero in processos_unicos:
                    continue

                # Contexto AMPLO: 1000 chars antes e depois
                start = max(0, match.start() - 1000)
                end = min(len(text), match.end() + 1000)
                contexto = text[start:end]
                contexto_lower = contexto.lower()

                # MÉTODO V2: Detectar tipo por PALAVRA-CHAVE no contexto
                tipo_encontrado = None
                classe_encontrada = None
                
                # Buscar palavras-chave no contexto
                if 'inventário' in contexto_lower or 'inventario' in contexto_lower:
                    tipo_encontrado = 'Inventário'
                    # Tentar extrair classe
                    classe_match = re.search(r'(INVENTÁRIO[^\n-]*|Inventário[^\n-]*)', contexto, re.IGNORECASE)
                    classe_encontrada = classe_match.group(1).strip()[:50] if classe_match else 'Inventário'
                    
                elif 'arrolamento' in contexto_lower:
                    tipo_encontrado = 'Inventário'  # Arrolamento é tipo de inventário
                    classe_encontrada = 'Arrolamento'
                    
                elif 'divórcio' in contexto_lower or 'divorcio' in contexto_lower:
                    tipo_encontrado = 'Divórcio'
                    # Tentar extrair classe com tipo (consensual/litigioso)
                    classe_match = re.search(r'(DIVÓRCIO\s+(?:CONSENSUAL|LITIGIOSO)|Divórcio\s+(?:Consensual|Litigioso))', contexto, re.IGNORECASE)
                    if classe_match:
                        classe_encontrada = classe_match.group(1).strip()
                    else:
                        classe_encontrada = 'Divórcio'

                # Se não encontrou tipo de interesse, pular
                if not tipo_encontrado:
                    continue
                
                # Verificar se tipo está na lista solicitada
                if tipos and tipo_encontrado not in tipos:
                    continue

                processos_unicos.add(numero)
                
                # Extrair código da comarca do número do processo
                codigo_comarca = numero.split('.')[-1]
                
                # Tentar extrair nome da comarca
                comarca = None
                comarca_match = re.search(r'(?:Comarca de|Foro de|Foro Central)\s+([A-ZÀ-Ú][a-zá-úÀ-Ú\s]+)', contexto)
                if comarca_match:
                    comarca = comarca_match.group(1).strip()
                else:
                    # Buscar nome da comarca pelo código
                    try:
                        from src.utils.comarcas import get_comarca_nome
                        comarca = get_comarca_nome(codigo_comarca, tribunal="TJSP")
                    except:
                        comarca = f"Código {codigo_comarca}"

                # Calcular relevância
                relevancia, score = calcular_relevancia(contexto)

                processos.append({
                    'numero': numero,
                    'tipo': tipo_encontrado,
                    'classe': classe_encontrada,
                    'comarca': comarca,
                    'codigo_comarca': codigo_comarca,
                    'partes': [],
                    'advogados': [],
                    'valor_causa': None,
                    'pagina_dje': i,
                    'tem_imovel': tem_imovel(contexto),
                    'esta_ativo': esta_ativo(contexto),
                    'relevancia': relevancia,
                    'score_relevancia': score
                })
    
    except Exception as e:
        if verbose:
            print(f"❌ Erro: {e}")
        return []

    if verbose:
        print(f"✅ {len(processos)} processos encontrados")

    return processos


if __name__ == "__main__":
    # Teste
    pdf = "data/dje_pdfs/dje_31-12-2024_cad12.pdf"
    processos = extrair_processos_dje_v2(pdf, verbose=True)
    
    from collections import Counter
    tipos = Counter(p['tipo'] for p in processos)
    
    print(f"\n📊 RESUMO:")
    for tipo, count in tipos.items():
        print(f"   {tipo}: {count}")
