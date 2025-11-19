"""
Sistema de Cache para API DataJud
Torna buscas INSTANTÂNEAS após primeira consulta
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional


CACHE_DIR = "data/cache_datajud"
CACHE_VALIDADE_HORAS = 24  # Cache válido por 24h


def obter_cache_path(tribunal: str, tipo_processo: str) -> str:
    """Gera path do arquivo de cache"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    filename = f"{tribunal}_{tipo_processo.replace(' ', '_')}.json"
    return os.path.join(CACHE_DIR, filename)


def ler_cache(tribunal: str, tipo_processo: str) -> Optional[Dict]:
    """
    Lê cache se existir e estiver válido

    Returns:
        Dict com processos ou None se cache inválido
    """
    cache_path = obter_cache_path(tribunal, tipo_processo)

    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache = json.load(f)

        # Verificar validade (24h)
        data_cache = datetime.fromisoformat(cache.get("data_atualizacao"))
        agora = datetime.now()

        if agora - data_cache > timedelta(hours=CACHE_VALIDADE_HORAS):
            print(f"⚠️ Cache expirado ({CACHE_VALIDADE_HORAS}h). Será atualizado.")
            return None

        print(f"✅ Cache válido! {len(cache.get('processos', []))} processos carregados")
        return cache

    except Exception as e:
        print(f"❌ Erro ao ler cache: {e}")
        return None


def salvar_cache(tribunal: str, tipo_processo: str, processos: List[Dict]) -> None:
    """Salva processos no cache"""
    cache_path = obter_cache_path(tribunal, tipo_processo)

    cache = {
        "tribunal": tribunal,
        "tipo_processo": tipo_processo,
        "total_processos": len(processos),
        "data_atualizacao": datetime.now().isoformat(),
        "processos": processos
    }

    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print(f"💾 Cache salvo: {len(processos)} processos ({os.path.getsize(cache_path) / 1024:.1f} KB)")


def filtrar_processos(
    processos: List[Dict],
    comarcas: Optional[List[str]] = None,
    valor_min: Optional[float] = None,
    valor_max: Optional[float] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
) -> List[Dict]:
    """
    Filtra processos do cache (INSTANTÂNEO!)

    Args:
        data_inicio: YYYY-MM-DD
        data_fim: YYYY-MM-DD
    """
    processos_filtrados = processos

    # Filtro por comarca
    if comarcas and len(comarcas) > 0:
        from src.utils.comarcas import FOROS_SAO_PAULO_CAPITAL, extrair_codigo_comarca

        processos_filtrados = []
        for p in processos:
            comarca = p.get("comarca", "")
            numero = p.get("numero", "")
            codigo_comarca = extrair_codigo_comarca(numero) if numero else None

            # Verificar São Paulo capital
            busca_sao_paulo = any(
                c.lower() in ["são paulo", "sao paulo", "sp capital"]
                for c in comarcas
            )

            if busca_sao_paulo and codigo_comarca in FOROS_SAO_PAULO_CAPITAL:
                processos_filtrados.append(p)
                continue

            # Verificação normal
            if any(c.lower() in comarca.lower() or comarca.lower() in c.lower() for c in comarcas):
                processos_filtrados.append(p)

        processos = processos_filtrados

    # Filtro por valor
    if valor_min is not None:
        processos = [p for p in processos if p.get("valor_causa") and p["valor_causa"] >= valor_min]

    if valor_max is not None:
        processos = [p for p in processos if p.get("valor_causa") and p["valor_causa"] <= valor_max]

    # Filtro por data de ajuizamento
    if data_inicio or data_fim:
        processos_filtrados = []
        for p in processos:
            data_ajuizamento = p.get("data_ajuizamento")
            if not data_ajuizamento:
                continue

            try:
                # DataJud retorna YYYY-MM-DD
                data_proc = datetime.strptime(data_ajuizamento[:10], "%Y-%m-%d")

                if data_inicio:
                    data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
                    if data_proc < data_inicio_dt:
                        continue

                if data_fim:
                    data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d")
                    if data_proc > data_fim_dt:
                        continue

                processos_filtrados.append(p)
            except:
                continue

        processos = processos_filtrados

    return processos


def limpar_cache_expirado() -> int:
    """Remove caches expirados"""
    if not os.path.exists(CACHE_DIR):
        return 0

    removidos = 0
    agora = datetime.now()

    for filename in os.listdir(CACHE_DIR):
        if not filename.endswith('.json'):
            continue

        filepath = os.path.join(CACHE_DIR, filename)

        try:
            with open(filepath, 'r') as f:
                cache = json.load(f)

            data_cache = datetime.fromisoformat(cache.get("data_atualizacao"))

            if agora - data_cache > timedelta(hours=CACHE_VALIDADE_HORAS):
                os.remove(filepath)
                removidos += 1
                print(f"🗑️ Removido cache expirado: {filename}")
        except:
            continue

    return removidos


def status_cache() -> Dict:
    """Retorna status do cache"""
    if not os.path.exists(CACHE_DIR):
        return {
            "total_arquivos": 0,
            "tamanho_total_mb": 0,
            "caches": []
        }

    caches = []
    tamanho_total = 0

    for filename in os.listdir(CACHE_DIR):
        if not filename.endswith('.json'):
            continue

        filepath = os.path.join(CACHE_DIR, filename)
        tamanho = os.path.getsize(filepath)
        tamanho_total += tamanho

        try:
            with open(filepath, 'r') as f:
                cache = json.load(f)

            caches.append({
                "arquivo": filename,
                "tribunal": cache.get("tribunal"),
                "tipo_processo": cache.get("tipo_processo"),
                "total_processos": cache.get("total_processos"),
                "data_atualizacao": cache.get("data_atualizacao"),
                "tamanho_kb": tamanho / 1024,
                "valido": (datetime.now() - datetime.fromisoformat(cache.get("data_atualizacao"))).total_seconds() / 3600 < CACHE_VALIDADE_HORAS
            })
        except:
            continue

    return {
        "total_arquivos": len(caches),
        "tamanho_total_mb": tamanho_total / 1024 / 1024,
        "validade_horas": CACHE_VALIDADE_HORAS,
        "caches": sorted(caches, key=lambda x: x["data_atualizacao"], reverse=True)
    }
