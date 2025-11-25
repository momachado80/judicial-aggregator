"""
Indexador de PDFs DJE - Processa todos os PDFs com OTIMIZAÇÃO e RESUME
"""
import os
import json
from datetime import datetime
from typing import List, Dict
import concurrent.futures
from src.scrapers.dje_parser import extrair_processos_dje


def processar_pdf_worker(pdf_path: str) -> List[Dict]:
    """Worker function para processar um único PDF (multiprocessing)"""
    try:
        pdf_nome = os.path.basename(pdf_path)
        # Processar SEM FILTROS e SEM LOGS VERBOSOS (mais rápido)
        processos = extrair_processos_dje(
            pdf_path=pdf_path,
            tipos=["Inventário", "Divórcio", "Arrolamento"],
            filtrar_imoveis=False,
            filtrar_ativos=False,
            comarcas_filtro=None,
            verbose=False  # Silent mode
        )

        # Adicionar metadados do PDF
        for p in processos:
            p["pdf_origem"] = pdf_nome
            try:
                p["data_pdf"] = pdf_nome.split("_")[1].replace(".pdf", "")
            except:
                p["data_pdf"] = "01-01-2000"

        return processos
    except Exception as e:
        print(f"  ❌ ERRO ao processar {os.path.basename(pdf_path)}: {e}")
        return []


def carregar_progresso(cache_path: str) -> tuple:
    """Carrega processos já salvos e lista de PDFs processados (para RESUME)"""
    if not os.path.exists(cache_path):
        return [], set()

    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            processos = data.get("processos", [])
            pdfs_processados = set(p.get("pdf_origem") for p in processos if p.get("pdf_origem"))
            return processos, pdfs_processados
    except Exception as e:
        print(f"⚠️  Erro ao ler cache: {e}. Começando do zero.")
        return [], set()


def salvar_cache_parcial(processos: List[Dict], total_pdfs: int, cache_path: str):
    """Salva cache parcialmente (batches)"""
    cache = {
        "total_processos": len(processos),
        "total_pdfs": total_pdfs,
        "data_indexacao": datetime.now().isoformat(),
        "processos": processos
    }

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    temp_path = cache_path + ".tmp"
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    os.replace(temp_path, cache_path)


def indexar_todos_pdfs(pdfs_dir: str = "data/dje_pdfs", cache_path: str = "data/dje_cache.json", limite_pdfs: int = None) -> Dict:
    """
    Processa TODOS os PDFs com OTIMIZAÇÃO (multiprocessing + batching + resume)

    Args:
        pdfs_dir: Diretório com PDFs
        cache_path: Caminho do arquivo de cache
        limite_pdfs: Limite de PDFs a processar (None = todos)

    Returns:
        {
            "total_processos": int,
            "total_pdfs": int,
            "data_indexacao": str,
            "processos": [...]
        }
    """
    print("\n" + "="*80)
    print("🚀 INDEXAÇÃO OTIMIZADA - Multiprocessing + Batching + Resume")
    print("="*80)

    if not os.path.exists(pdfs_dir):
        raise FileNotFoundError(f"Diretório de PDFs não encontrado: {pdfs_dir}")

    # 1. Listar todos os PDFs de CADERNOS 11, 12, 13, 14 (Capital + Interior)
    todos_pdfs = sorted([
        os.path.join(pdfs_dir, f)
        for f in os.listdir(pdfs_dir)
        if f.endswith('.pdf') and not f.startswith('teste') and any(f'cad{c}' in f for c in ['11', '12', '13', '14'])
    ], reverse=True)

    if limite_pdfs:
        todos_pdfs = todos_pdfs[:limite_pdfs]
        print(f"⚠️  MODO LIMITADO: {limite_pdfs} PDFs")

    print(f"📦 Total de PDFs disponíveis: {len(todos_pdfs)}")

    # 2. Carregar progresso anterior (RESUME)
    todos_processos, pdfs_ja_processados = carregar_progresso(cache_path)

    # Filtrar PDFs que faltam processar
    pdfs_para_processar = [
        p for p in todos_pdfs
        if os.path.basename(p) not in pdfs_ja_processados
    ]

    print(f"🔄 Retomando: {len(pdfs_ja_processados)} PDFs já processados")
    print(f"⏳ Restam: {len(pdfs_para_processar)} PDFs para processar")

    if not pdfs_para_processar:
        print("✅ Nada a fazer! Todos os PDFs já foram processados.")
        # Aplicar deduplicação final
        processos_unicos = {}
        for p in todos_processos:
            numero = p["numero"]
            if numero not in processos_unicos:
                processos_unicos[numero] = p
        processos_deduplicated = list(processos_unicos.values())

        cache = {
            "total_processos": len(processos_deduplicated),
            "total_pdfs": len(todos_pdfs),
            "data_indexacao": datetime.now().isoformat(),
            "processos": processos_deduplicated
        }
        salvar_cache_parcial(processos_deduplicated, len(todos_pdfs), cache_path)
        return cache

    # 3. Processamento com multiprocessing em BATCHES
    BATCH_SIZE = 100  # Production batch size
    TIMEOUT_POR_PDF = 180  # 3 minutos por PDF
    max_workers = 2  # 2 workers for speed

    print(f"⚡ Workers: {max_workers} | Batch: {BATCH_SIZE} PDFs")
    print(f"🔥 Logs silenciados para velocidade!\n")

    chunks = [pdfs_para_processar[i:i + BATCH_SIZE] for i in range(0, len(pdfs_para_processar), BATCH_SIZE)]
    total_chunks = len(chunks)

    for i, chunk in enumerate(chunks, 1):
        print(f"📦 Lote {i}/{total_chunks} ({len(chunk)} PDFs)...")

        novos_processos = []

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(processar_pdf_worker, pdf): pdf for pdf in chunk}

            for future in concurrent.futures.as_completed(futures):
                pdf_path = futures[future]
                try:
                    resultado = future.result(timeout=TIMEOUT_POR_PDF)
                    if resultado:
                        novos_processos.extend(resultado)
                except concurrent.futures.TimeoutError:
                    print(f"  ⏰ TIMEOUT: {os.path.basename(pdf_path)}")
                except Exception as e:
                    print(f"  ❌ ERRO: {os.path.basename(pdf_path)} - {e}")

        # Adicionar ao total
        todos_processos.extend(novos_processos)

        # SALVAR PARCIALMENTE (a cada batch)
        print(f"  💾 Salvando ({len(todos_processos)} processos totais)...\n")
        salvar_cache_parcial(todos_processos, len(todos_pdfs), cache_path)

        # Limpar memória
        import gc
        gc.collect()

    # 4. Deduplicação FINAL
    print("\n" + "="*80)
    print("🔍 Aplicando deduplicação final...")
    print(f"   Total ANTES: {len(todos_processos)} processos")

    processos_unicos = {}
    for p in todos_processos:
        numero = p["numero"]
        if numero not in processos_unicos:
            processos_unicos[numero] = p

    processos_deduplicated = list(processos_unicos.values())
    processos_removidos = len(todos_processos) - len(processos_deduplicated)

    print(f"   Total DEPOIS: {len(processos_deduplicated)} processos")
    print(f"   🗑️ Removidos {processos_removidos} duplicados")

    # Salvar FINAL
    cache = {
        "total_processos": len(processos_deduplicated),
        "total_pdfs": len(todos_pdfs),
        "data_indexacao": datetime.now().isoformat(),
        "processos": processos_deduplicated
    }
    salvar_cache_parcial(processos_deduplicated, len(todos_pdfs), cache_path)

    print("\n" + "="*80)
    print("✅ INDEXAÇÃO CONCLUÍDA!")
    print("="*80)
    print(f"📊 Total de processos únicos: {len(processos_deduplicated)}")
    print(f"📄 PDFs processados: {len(todos_pdfs)}")
    print(f"🗑️ Duplicados removidos: {processos_removidos}")
    print(f"💾 Cache salvo em: {cache_path}")
    print(f"📦 Tamanho: {os.path.getsize(cache_path) / 1024 / 1024:.2f} MB")
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
