import pdfplumber
import re
from typing import List, Dict, Optional
from datetime import datetime
from src.utils.comarcas import FOROS_SAO_PAULO_CAPITAL, get_comarca_nome

# Palavras-chave que indicam presença de IMÓVEIS
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

# Palavras que indicam processo ativo/urgente
PALAVRAS_URGENCIA = [
    "penhora", "leilão", "leilao", "hasta pública", "hasta publica",
    "adjudicação", "adjudicacao", "alienação judicial", "alienacao judicial",
    "partilha", "avaliação", "avaliacao", "inventariante", "arrolamento"
]

# Palavras que indicam processo EXTINTO/ARQUIVADO
PALAVRAS_EXTINTO = [
    "extinto", "arquivado", "baixado", "sentença de extinção",
    "sentenca de extincao", "processo extinto", "arquivamento",
    "cancelado", "suspenso", "sobrestado"
]

def tem_imovel(texto: str) -> bool:
    """Verifica se o texto menciona imóveis"""
    texto_lower = texto.lower()
    return any(palavra.lower() in texto_lower for palavra in PALAVRAS_IMOVEIS)

def esta_ativo(texto: str) -> bool:
    """Verifica se processo está ativo (não extinto/arquivado)"""
    texto_lower = texto.lower()
    # Se menciona palavras de extinção, retorna False
    if any(palavra.lower() in texto_lower for palavra in PALAVRAS_EXTINTO):
        return False
    return True

def calcular_relevancia_imovel(texto: str) -> tuple:
    """Calcula score de relevância baseado em imóveis e urgência"""
    texto_lower = texto.lower()

    tem_imovel_flag = tem_imovel(texto)
    tem_urgencia = any(palavra.lower() in texto_lower for palavra in PALAVRAS_URGENCIA)

    if tem_imovel_flag and tem_urgencia:
        return ("Altíssima", 1.0)
    elif tem_imovel_flag:
        return ("Alta", 0.8)
    elif tem_urgencia:
        return ("Média", 0.5)
    else:
        return ("Baixa", 0.2)

def extrair_processos_dje(
    pdf_path: str,
    tipos: List[str] = ["Inventário", "Divórcio"],
    filtrar_imoveis: bool = True,
    filtrar_ativos: bool = True,
    comarcas_filtro: Optional[List[str]] = None,
    valor_min: Optional[float] = None,
    valor_max: Optional[float] = None
) -> List[Dict]:
    """
    Extrai processos do DJE com filtros avançados

    Args:
        pdf_path: Caminho do PDF
        tipos: Tipos de processo a buscar
        filtrar_imoveis: Se True, retorna apenas processos com imóveis
        filtrar_ativos: Se True, exclui processos extintos/arquivados
        comarcas_filtro: Lista de comarcas para filtrar (None = todas)
        valor_min: Valor mínimo da causa
        valor_max: Valor máximo da causa
    """
    print(f"📄 Parseando: {pdf_path}")
    print(f"   🏠 Filtrar imóveis: {filtrar_imoveis}")
    print(f"   ✅ Filtrar ativos: {filtrar_ativos}")
    if comarcas_filtro:
        print(f"   📍 Comarcas: {', '.join(comarcas_filtro)}")

    processos = []
    processos_unicos = set()  # Para evitar duplicatas
    processos_rejeitados = {"sem_imovel": 0, "extinto": 0, "comarca": 0, "valor": 0}
    
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
                start = max(0, match.start() - 2000)  # Aumentei contexto
                end = min(len(text), match.end() + 2000)
                contexto = text[start:end]

                # Verificar se menciona os tipos procurados
                tipo_encontrado = None
                for tipo in tipos:
                    if tipo.lower() in contexto.lower():
                        tipo_encontrado = tipo
                        break

                if not tipo_encontrado:
                    continue

                # FILTRO 1: Verificar se tem imóveis (se filtro ativado)
                if filtrar_imoveis and not tem_imovel(contexto):
                    processos_rejeitados["sem_imovel"] += 1
                    continue

                # FILTRO 2: Verificar se está ativo (se filtro ativado)
                if filtrar_ativos and not esta_ativo(contexto):
                    processos_rejeitados["extinto"] += 1
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
                    if comarca_match:
                        comarca = comarca_match.group(1).strip()
                    else:
                        # Buscar nome da comarca pelo código
                        from src.utils.comarcas import get_comarca_nome
                        comarca = get_comarca_nome(codigo_comarca, tribunal="TJSP")

                # FILTRO 3: Filtrar por comarca (se especificado)
                if comarcas_filtro:
                    comarca_aceita = False

                    # Verificar se São Paulo está nos filtros
                    busca_sao_paulo = any(
                        c.lower() in ["são paulo", "sao paulo", "sp capital", "são paulo (capital)", "sao paulo (capital)"]
                        for c in comarcas_filtro
                    )

                    # Se buscar São Paulo, verificar pelo CÓDIGO da comarca
                    if busca_sao_paulo and codigo_comarca in FOROS_SAO_PAULO_CAPITAL:
                        comarca_aceita = True

                    # Verificação normal por nome de comarca
                    if not comarca_aceita and comarca:
                        comarca_aceita = any(
                            c.lower() in comarca.lower() or comarca.lower() in c.lower()
                            for c in comarcas_filtro
                        )

                    if not comarca_aceita:
                        processos_rejeitados["comarca"] += 1
                        continue
                
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
                
                # Extrair valor da causa
                valor_causa_float = None
                valor_match = re.search(r'R\$\s*([\d.,]+)', contexto)
                if valor_match:
                    valor_str = valor_match.group(1)
                    # Converter para float
                    try:
                        valor_causa_float = float(valor_str.replace('.', '').replace(',', '.'))
                    except:
                        valor_causa_float = None

                # FILTRO 4: Filtrar por valor da causa (se especificado)
                if valor_min is not None and valor_causa_float is not None:
                    if valor_causa_float < valor_min:
                        processos_rejeitados["valor"] += 1
                        continue

                if valor_max is not None and valor_causa_float is not None:
                    if valor_causa_float > valor_max:
                        processos_rejeitados["valor"] += 1
                        continue

                # Calcular relevância baseada em imóveis
                relevancia, score = calcular_relevancia_imovel(contexto)

                processos.append({
                    'numero': numero,
                    'tipo': tipo_encontrado,
                    'classe': classe,
                    'comarca': comarca,
                    'codigo_comarca': codigo_comarca,
                    'partes': partes,
                    'advogados': advogados,
                    'valor_causa': valor_causa_float,
                    'pagina_dje': i,
                    'tem_imovel': tem_imovel(contexto),
                    'esta_ativo': esta_ativo(contexto),
                    'relevancia': relevancia,
                    'score_relevancia': score
                })
    
    # Relatório de filtros
    total_rejeitados = sum(processos_rejeitados.values())
    print(f"\n✅ {len(processos)} processos APROVADOS nos filtros")

    if total_rejeitados > 0:
        print(f"❌ {total_rejeitados} processos REJEITADOS:")
        if processos_rejeitados["sem_imovel"] > 0:
            print(f"   🏠 {processos_rejeitados['sem_imovel']} sem menção a imóveis")
        if processos_rejeitados["extinto"] > 0:
            print(f"   ⚰️  {processos_rejeitados['extinto']} extintos/arquivados")
        if processos_rejeitados["comarca"] > 0:
            print(f"   📍 {processos_rejeitados['comarca']} fora das comarcas selecionadas")
        if processos_rejeitados["valor"] > 0:
            print(f"   💰 {processos_rejeitados['valor']} fora do range de valor")

    return processos

if __name__ == "__main__":
    from datetime import date

    pdf_path = "data/dje_pdfs/dje_15-11-2025_cad11.pdf"

    print("="*80)
    print("🧪 TESTE - Parser DJE com Filtros Avançados")
    print("="*80)

    # Teste 1: Apenas processos com imóveis
    print("\n📋 TESTE 1: Apenas processos com IMÓVEIS")
    processos = extrair_processos_dje(
        pdf_path,
        tipos=["Inventário", "Divórcio"],
        filtrar_imoveis=True,
        filtrar_ativos=True
    )

    if processos:
        print(f"\n✅ {len(processos)} processos encontrados com imóveis")

        from collections import Counter
        tipos_count = Counter(p['tipo'] for p in processos)
        relevancia_count = Counter(p['relevancia'] for p in processos)

        print(f"\n📊 Por tipo:")
        for tipo, count in tipos_count.items():
            print(f"   {tipo}: {count}")

        print(f"\n🎯 Por relevância:")
        for rel, count in relevancia_count.items():
            print(f"   {rel}: {count}")

        print(f"\n🔍 PRIMEIROS 5 PROCESSOS:")
        for p in processos[:5]:
            print(f"\n{'='*80}")
            print(f"Processo: {p['numero']}")
            print(f"Tipo: {p['tipo']} | Relevância: {p['relevancia']} ({p['score_relevancia']})")
            print(f"Comarca: {p['comarca']}")
            print(f"Tem imóvel: {'✅' if p['tem_imovel'] else '❌'}")
            print(f"Ativo: {'✅' if p['esta_ativo'] else '❌'}")
            if p['valor_causa']:
                print(f"Valor: R$ {p['valor_causa']:,.2f}")
            if p['partes']:
                print(f"Partes: {', '.join(p['partes'][:2])}")

    # Teste 2: Filtrar por comarca
    print("\n" + "="*80)
    print("📋 TESTE 2: Apenas PIRACICABA com imóveis")
    processos_piracicaba = extrair_processos_dje(
        pdf_path,
        tipos=["Inventário", "Divórcio"],
        filtrar_imoveis=True,
        filtrar_ativos=True,
        comarcas_filtro=["Piracicaba"]
    )
    print(f"✅ {len(processos_piracicaba)} processos em Piracicaba com imóveis")

    # Teste 3: Filtrar por valor
    print("\n" + "="*80)
    print("📋 TESTE 3: Valor entre R$ 100k e R$ 1M com imóveis")
    processos_valor = extrair_processos_dje(
        pdf_path,
        tipos=["Inventário", "Divórcio"],
        filtrar_imoveis=True,
        filtrar_ativos=True,
        valor_min=100000,
        valor_max=1000000
    )
    print(f"✅ {len(processos_valor)} processos no range de valor")
