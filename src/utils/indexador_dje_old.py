"""
Indexador de PDFs DJE - Versão V2 com parser melhorado
"""
import os
import json
from datetime import datetime
from typing import List, Dict
import concurrent.futures
from src.scrapers.dje_parser_v2 import extrair_processos_dje_v2


def processar_pdf_worker(pdf_path: str) -> List[Dict]:
    try:
        pdf_nome = os.path.basename(pdf_path)
        processos = extrair_processos_dje_v2(
            pdf_path=pdf_path,
            tipos=["Inventário", "Divórcio"],
            filtrar_imoveis=False,
            filtrar_ativos=False,
            verbose=False
        )
        for p in processos:
            p["pdf_origem"] = pdf_nome
            try:
                p["data_pdf"] = pdf_nome.split("_")[1].replace(".pdf", "")
            except:
                p["data_pdf"] = "01-01-2000"
        return processos
    except Exception as e:
        print(f"  ❌ ERRO: {os.path.basename(pdf_path)}: {e}")
        return []


def indexar_todos_pdfs(pdfs_dir: str = "data/dje_pdfs", cache_path: str = "data/dje_cache.json", limite_pdfs: int = None) -> Dict:
    print("\n" + "="*80)
    print("🚀 INDEXAÇÃO V2 - Parser Melhorado")
    print("="*80)

    if not os.path.exists(pdfs_dir):
        raise FileNotFoundError(f"Diretório não encontrado: {pdfs_dir}")

    todos_pdfs = sorted([
        os.path.join(pdfs_dir, f)
        for f in os.listdir(pdfs_dir)
        if f.endswith('.pdf') and any(f'cad{c}' in f for c in ['11', '12', '13', '14'])
    ], reverse=True)

    if limite_pdfs:
        todos_pdfs = todos_pdfs[:limite_pdfs]
        print(f"⚠️  LIMITE: {limite_pdfs} PDFs")

    print(f"📦 Total de PDFs: {len(todos_pdfs)}")

    if os.path.exists(cache_path):
        os.remove(cache_path)
        print("🗑️  Cache anterior removido")

    todos_processos = []
    BATCH_SIZE = 50
    max_workers = 2

    print(f"⚡ Workers: {max_workers} | Batch: {BATCH_SIZE}\n")

    chunks = [todos_pdfs[i:i + BATCH_SIZE] for i in range(0, len(todos_pdfs), BATCH_SIZE)]

    for i, chunk in enumerate(chunks, 1):
        print(f"📦 Lote {i}/{len(chunks)} ({len(chunk)} PDFs)...")

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(processar_pdf_worker, pdf): pdf for pdf in chunk}
            for future in concurrent.futures.as_completed(futures):
                try:
                    resultado = future.result(timeout=180)
                    if resultado:
                        todos_processos.extend(resultado)
                except Exception as e:
                    pass

        print(f"  📊 Total parcial: {len(todos_processos)} processos\n")

    print("🔍 Removendo duplicatas...")
    processos_unicos = {}
    for p in todos_processos:
        numero = p["numero"]
        if numero not in processos_unicos:
            processos_unicos[numero] = p

    processos_final = list(processos_unicos.values())
    print(f"✅ {len(processos_final)} únicos (removidos {len(todos_processos) - len(processos_final)} duplicados)")

    cache = {
        "total_processos": len(processos_final),
        "total_pdfs": len(todos_pdfs),
        "data_indexacao": datetime.now().isoformat(),
        "processos": processos_final
    }

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Salvo: {cache_path}")
    return cache


def ler_cache(cache_path: str = "data/dje_cache.json") -> Dict:
    if not os.path.exists(cache_path):
        raise FileNotFoundError(f"Cache não encontrado: {cache_path}")
    with open(cache_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def filtrar_processos_cache(cache: Dict, tipos: List[str] = None, comarcas: List[str] = None,
    apenas_imoveis: bool = True, apenas_ativos: bool = True,
    valor_min: float = None, valor_max: float = None,
    data_inicio: str = None, data_fim: str = None) -> List[Dict]:
    processos = cache["processos"]

    if data_inicio or data_fim:
        from datetime import datetime as dt
        processos_filtrados = []
        for p in processos:
            data_pdf = p.get("data_pdf")
            if not data_pdf:
                continue
            try:
                data_processo = dt.strptime(data_pdf, "%d-%m-%Y")
                if data_inicio and data_processo < dt.strptime(data_inicio, "%Y-%m-%d"):
                    continue
                if data_fim and data_processo > dt.strptime(data_fim, "%Y-%m-%d"):
                    continue
                processos_filtrados.append(p)
            except:
                continue
        processos = processos_filtrados

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
            busca_sp = any(c.lower() in ["são paulo", "sao paulo", "são paulo (capital)"] for c in comarcas)
            if busca_sp and codigo_comarca in FOROS_SAO_PAULO_CAPITAL:
                processos_filtrados.append(p)
                continue
            if any(c.lower() in comarca.lower() for c in comarcas):
                processos_filtrados.append(p)
        processos = processos_filtrados

    if valor_min is not None:
        processos = [p for p in processos if p.get("valor_causa") and p["valor_causa"] >= valor_min]
    if valor_max is not None:
        processos = [p for p in processos if p.get("valor_causa") and p["valor_causa"] <= valor_max]

    return processos


def ordenar_processos(processos: List[Dict], ordenar_por: str = "relevancia_desc") -> List[Dict]:
    from datetime import datetime as dt
    if ordenar_por == "relevancia_desc":
        return sorted(processos, key=lambda p: p.get("score_relevancia", 0), reverse=True)
    elif ordenar_por == "data_desc":
        def get_data(p):
            try:
                return dt.strptime(p.get("data_pdf", "01-01-2000"), "%d-%m-%Y")
            except:
                return dt(2000, 1, 1)
        return sorted(processos, key=get_data, reverse=True)
    return processos
