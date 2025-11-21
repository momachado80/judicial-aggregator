"""
Indexador de PDFs DJE - Processa todos os PDFs UMA VEZ e salva em cache JSON
"""
import os
import json
from datetime import datetime
from typing import List, Dict
from src.scrapers.dje_parser import extrair_processos_dje


def indexar_todos_pdfs(pdfs_dir: str = "data/dje_pdfs", cache_path: str = "data/dje_cache.json", limite_pdfs: int = None) -> Dict:
    """
    Processa TODOS os PDFs (ou limite especificado) e salva em cache JSON

    Args:
        pdfs_dir: Diretório com PDFs
        cache_path: Caminho do arquivo de cache
        limite_pdfs: Limite de PDFs a processar (None = todos). Use 10-15 para evitar OOM no Railway.

    Returns:
        {
            "total_processos": int,
            "total_pdfs": int,
            "data_indexacao": str,
            "processos": [...]
        }
    """
    print("\n" + "="*80)
    print("🚀 INDEXAÇÃO DE PDFs DJE - PROCESSAMENTO ÚNICO")
    print("="*80)

    if not os.path.exists(pdfs_dir):
        raise FileNotFoundError(f"Diretório de PDFs não encontrado: {pdfs_dir}")

    # Listar todos os PDFs de CADERNO 12 (Distribuições - melhor fonte para Inventário/Divórcio)
    # Ordenados do mais recente para o mais antigo
    todos_pdfs = sorted([
        os.path.join(pdfs_dir, f)
        for f in os.listdir(pdfs_dir)
        if f.endswith('.pdf') and not f.startswith('teste') and 'cad12' in f
    ], reverse=True)  # Mais recentes primeiro

    # Aplicar limite se especificado
    if limite_pdfs:
        todos_pdfs = todos_pdfs[:limite_pdfs]
        print(f"⚠️  MODO LIMITADO: Processando apenas os {limite_pdfs} PDFs mais recentes (de {len(todos_pdfs)} disponíveis)")

    print(f"\n📦 {len(todos_pdfs)} PDFs encontrados")
    print("⏳ Processando... (isso pode levar 10-20 minutos, mas só precisa ser feito UMA VEZ)\n")

    todos_processos = []
    pdfs_processados = 0

    for i, pdf_path in enumerate(todos_pdfs, 1):
        pdf_nome = os.path.basename(pdf_path)
        print(f"[{i}/{len(todos_pdfs)}] {pdf_nome}")

        try:
            # Processar SEM FILTROS - capturar TUDO
            processos = extrair_processos_dje(
                pdf_path=pdf_path,
                tipos=["Inventário", "Divórcio", "Arrolamento"],
                filtrar_imoveis=False,  # Captura todos
                filtrar_ativos=False,   # Captura todos
                comarcas_filtro=None    # Captura todas
            )

            # Adicionar metadados do PDF
            for p in processos:
                p["pdf_origem"] = pdf_nome
                p["data_pdf"] = pdf_nome.split("_")[1].replace(".pdf", "")

            todos_processos.extend(processos)
            pdfs_processados += 1
            print(f"  ✅ {len(processos)} processos extraídos\n")

        except Exception as e:
            print(f"  ❌ ERRO: {e}\n")
            continue

    # Criar estrutura do cache
    cache = {
        "total_processos": len(todos_processos),
        "total_pdfs": pdfs_processados,
        "data_indexacao": datetime.now().isoformat(),
        "processos": todos_processos
    }

    # Salvar cache
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print("\n" + "="*80)
    print("✅ INDEXAÇÃO CONCLUÍDA!")
    print("="*80)
    print(f"📊 Total de processos indexados: {len(todos_processos)}")
    print(f"📄 PDFs processados: {pdfs_processados}/{len(todos_pdfs)}")
    print(f"💾 Cache salvo em: {cache_path}")
    print(f"📦 Tamanho do arquivo: {os.path.getsize(cache_path) / 1024 / 1024:.2f} MB")
    print("="*80)

    return cache


def ler_cache(cache_path: str = "data/dje_cache.json") -> Dict:
    """Lê o cache de processos"""
    if not os.path.exists(cache_path):
        raise FileNotFoundError(
            f"Cache não encontrado em {cache_path}. "
            f"Execute indexar_todos_pdfs() primeiro."
        )

    with open(cache_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def filtrar_processos_cache(
    cache: Dict,
    tipos: List[str] = None,
    comarcas: List[str] = None,
    apenas_imoveis: bool = True,
    apenas_ativos: bool = True,
    valor_min: float = None,
    valor_max: float = None,
    data_inicio: str = None,
    data_fim: str = None
) -> List[Dict]:
    """
    Filtra processos do cache (INSTANTÂNEO)

    Esta função é EXTREMAMENTE RÁPIDA porque apenas filtra dados já processados

    Args:
        data_inicio: Data no formato YYYY-MM-DD (ex: 2024-01-01)
        data_fim: Data no formato YYYY-MM-DD (ex: 2024-02-01)
    """
    processos = cache["processos"]

    # Filtrar por data do DJE (se especificado)
    if data_inicio or data_fim:
        from datetime import datetime

        processos_filtrados = []
        for p in processos:
            data_pdf = p.get("data_pdf")  # Formato: DD-MM-YYYY
            if not data_pdf:
                continue

            try:
                # Converter DD-MM-YYYY para datetime
                data_processo = datetime.strptime(data_pdf, "%d-%m-%Y")

                # Comparar com range
                if data_inicio:
                    data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
                    if data_processo < data_inicio_dt:
                        continue

                if data_fim:
                    data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d")
                    if data_processo > data_fim_dt:
                        continue

                processos_filtrados.append(p)
            except:
                continue

        processos = processos_filtrados

    # Aplicar filtros
    if tipos:
        processos = [p for p in processos if p.get("tipo") in tipos]

    if apenas_imoveis:
        processos = [p for p in processos if p.get("tem_imovel") == True]

    if apenas_ativos:
        processos = [p for p in processos if p.get("esta_ativo") == True]

    if comarcas:
        from src.utils.comarcas import FOROS_SAO_PAULO_CAPITAL

        processos_filtrados = []
        for p in processos:
            comarca = p.get("comarca", "")
            codigo_comarca = p.get("codigo_comarca", "")

            # Verificar se busca São Paulo
            busca_sao_paulo = any(
                c.lower() in ["são paulo", "sao paulo", "sp capital", "são paulo (capital)"]
                for c in comarcas
            )

            # Se buscar São Paulo, aceitar códigos da capital
            if busca_sao_paulo and codigo_comarca in FOROS_SAO_PAULO_CAPITAL:
                processos_filtrados.append(p)
                continue

            # Verificação normal por nome
            if any(c.lower() in comarca.lower() or comarca.lower() in c.lower() for c in comarcas):
                processos_filtrados.append(p)

        processos = processos_filtrados

    if valor_min is not None:
        processos = [p for p in processos if p.get("valor_causa") and p["valor_causa"] >= valor_min]

    if valor_max is not None:
        processos = [p for p in processos if p.get("valor_causa") and p["valor_causa"] <= valor_max]

    return processos


def ordenar_processos(
    processos: List[Dict],
    ordenar_por: str = "relevancia_desc"
) -> List[Dict]:
    """
    Ordena processos segundo critério especificado

    Args:
        processos: Lista de processos para ordenar
        ordenar_por: Critério de ordenação
            - "relevancia_desc": Alta relevância primeiro (padrão)
            - "relevancia_asc": Baixa relevância primeiro
            - "data_desc": Mais recente primeiro (por data do DJE)
            - "data_asc": Mais antigo primeiro (por data do DJE)
            - "valor_desc": Maior valor de causa primeiro
            - "valor_asc": Menor valor de causa primeiro

    Returns:
        Lista ordenada de processos
    """
    from datetime import datetime

    if ordenar_por == "relevancia_desc":
        # Alta -> Baixa (0.8 -> 0.2)
        return sorted(processos, key=lambda p: p.get("score_relevancia", 0), reverse=True)

    elif ordenar_por == "relevancia_asc":
        # Baixa -> Alta (0.2 -> 0.8)
        return sorted(processos, key=lambda p: p.get("score_relevancia", 0), reverse=False)

    elif ordenar_por == "data_desc":
        # Mais recente primeiro
        def get_data(p):
            data_pdf = p.get("data_pdf", "01-01-2000")
            try:
                return datetime.strptime(data_pdf, "%d-%m-%Y")
            except:
                return datetime(2000, 1, 1)

        return sorted(processos, key=get_data, reverse=True)

    elif ordenar_por == "data_asc":
        # Mais antigo primeiro
        def get_data(p):
            data_pdf = p.get("data_pdf", "01-01-2000")
            try:
                return datetime.strptime(data_pdf, "%d-%m-%Y")
            except:
                return datetime(2000, 1, 1)

        return sorted(processos, key=get_data, reverse=False)

    elif ordenar_por == "valor_desc":
        # Maior valor primeiro
        return sorted(
            processos,
            key=lambda p: p.get("valor_causa") if p.get("valor_causa") is not None else -1,
            reverse=True
        )

    elif ordenar_por == "valor_asc":
        # Menor valor primeiro
        return sorted(
            processos,
            key=lambda p: p.get("valor_causa") if p.get("valor_causa") is not None else float('inf'),
            reverse=False
        )

    else:
        # Se ordenação inválida, retornar sem ordenar
        return processos


if __name__ == "__main__":
    # Executar indexação
    cache = indexar_todos_pdfs()

    # Teste de velocidade
    print("\n🧪 TESTANDO VELOCIDADE DE BUSCA...")
    import time

    start = time.time()
    resultados = filtrar_processos_cache(
        cache,
        tipos=["Inventário", "Divórcio"],
        comarcas=["São Paulo"],
        apenas_imoveis=True,
        apenas_ativos=True
    )
    elapsed = time.time() - start

    print(f"✅ Busca concluída em {elapsed*1000:.0f}ms")
    print(f"📊 {len(resultados)} processos encontrados")
    print("🚀 Velocidade: INSTANTÂNEA!")
