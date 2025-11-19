from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import requests
from src.utils.comarcas import get_comarca_nome, extrair_codigo_comarca, formatar_numero_cnj
from src.utils.cache_datajud import ler_cache, salvar_cache, filtrar_processos, status_cache

router = APIRouter()

class BuscarProcessosRequest(BaseModel):
    tribunais: List[str]
    tipos_processo: List[str]
    comarcas: Optional[List[str]] = None
    valor_causa_min: Optional[float] = None
    valor_causa_max: Optional[float] = None
    data_inicio: Optional[str] = None  # YYYY-MM-DD
    data_fim: Optional[str] = None     # YYYY-MM-DD
    ano: Optional[int] = None
    quantidade: int = 50
    usar_cache: bool = True  # Novo: permite desabilitar cache

TIPOS_PROCESSO_MAPPING = {
    "Inventário": 39,
    "Divórcio Litigioso": 12541, 
    "Divórcio Consensual": 12372
}

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="


async def _buscar_api_cnj(tribunal: str, tipo: str, quantidade: int = 1000) -> List[Dict]:
    """
    Busca processos diretamente na API do CNJ (SEM CACHE)

    Returns:
        Lista de processos
    """
    tipo_cod = TIPOS_PROCESSO_MAPPING.get(tipo, "289")

    url = f"https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal.lower()}/_search"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"APIKey {DATAJUD_API_KEY}"
    }

    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"classe.codigo": tipo_cod}},
                    {"term": {"tribunal": tribunal}}
                ]
            }
        },
        "size": min(quantidade, 1000),
        "sort": [{"dataAjuizamento": {"order": "desc"}}]
    }

    try:
        response = requests.post(url, headers=headers, json=query, timeout=30)

        if response.status_code != 200:
            print(f"❌ Erro API CNJ: {response.status_code}")
            return []

        data = response.json()
        hits = data.get("hits", {}).get("hits", [])

        print(f"✅ API CNJ retornou {len(hits)} processos")

        processos = []
        for hit in hits:
            source = hit.get("_source", {})
            numero = source.get("numeroProcesso", "")

            if not numero:
                continue

            # Extrair comarca
            codigo_comarca = extrair_codigo_comarca(numero)
            nome_comarca = get_comarca_nome(codigo_comarca, tribunal)

            # Número limpo (sem formatação)
            numero_limpo = numero.replace("-", "").replace(".", "")

            # URL corrigida para TJSP
            url_tjsp = None
            if tribunal == "TJSP":
                url_tjsp = f"https://esaj.tjsp.jus.br/cpopg/show.do?processo.codigo={numero_limpo}"

            processo = {
                "numero": numero,
                "tribunal": tribunal,
                "tipo": tipo,
                "comarca": nome_comarca,
                "codigo_comarca": codigo_comarca,
                "valor_causa": source.get("valorCausa"),
                "data_ajuizamento": source.get("dataAjuizamento"),
                "url_tjsp": url_tjsp
            }

            processos.append(processo)

        return processos

    except Exception as e:
        print(f"❌ Erro ao chamar API CNJ: {e}")
        return []

@router.post("/buscar-processos")
async def buscar_processos(request: BuscarProcessosRequest):
    """
    🚀 Busca processos na API DataJud com CACHE INTELIGENTE

    VELOCIDADE:
    - Primeira busca: 5-30s (chama API CNJ)
    - Buscas seguintes: < 1s (usa cache local válido por 24h)

    FILTROS:
    - Tribunal, tipo, comarca, valor, data
    - Expandir "São Paulo" para todos foros da capital
    """
    try:
        print(f"\n{'='*80}")
        print(f"🔍 BUSCA API DATAJUD")
        print(f"Comarcas: {request.comarcas}")
        print(f"Cache: {'Habilitado' if request.usar_cache else 'Desabilitado'}")
        print(f"{'='*80}")

        # Expandir "São Paulo" para todos os foros da capital
        from src.utils.comarcas import expandir_sao_paulo
        if request.comarcas:
            request.comarcas = expandir_sao_paulo(request.comarcas)

        todos_processos = []

        for tribunal in request.tribunais:
            for tipo in request.tipos_processo:
                # TENTAR LER DO CACHE PRIMEIRO
                cache_data = None
                if request.usar_cache:
                    cache_data = ler_cache(tribunal, tipo)

                if cache_data:
                    # CACHE VÁLIDO - BUSCA INSTANTÂNEA!
                    print(f"⚡ Usando cache para {tribunal} - {tipo}")
                    processos_cache = cache_data.get("processos", [])
                else:
                    # CACHE INVÁLIDO - CHAMAR API CNJ
                    print(f"🌐 Chamando API CNJ para {tribunal} - {tipo}...")
                    processos_cache = await _buscar_api_cnj(tribunal, tipo, request.quantidade)

                    # Salvar no cache
                    if processos_cache:
                        salvar_cache(tribunal, tipo, processos_cache)

                # Adicionar processos
                todos_processos.extend(processos_cache)

        # APLICAR FILTROS (comarca, valor, data) - INSTANTÂNEO!
        print(f"\n📊 Total antes de filtros: {len(todos_processos)}")

        processos_filtrados = filtrar_processos(
            processos=todos_processos,
            comarcas=request.comarcas,
            valor_min=request.valor_causa_min,
            valor_max=request.valor_causa_max,
            data_inicio=request.data_inicio,
            data_fim=request.data_fim
        )

        print(f"✅ Total após filtros: {len(processos_filtrados)}")
        print(f"{'='*80}\n")

        # Limitar quantidade
        resultado = processos_filtrados[:request.quantidade]

        return resultado
        
    except Exception as e:
        print(f"💥 ERRO: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/status")
async def cache_status_api():
    """
    📊 Status do cache DataJud

    Retorna informações sobre caches existentes:
    - Total de arquivos
    - Tamanho total
    - Validade (24h)
    - Lista de caches com detalhes
    """
    return status_cache()


@router.post("/cache/limpar")
async def limpar_cache_api():
    """
    🗑️ Limpar caches expirados (> 24h)

    Remove apenas caches expirados.
    Caches válidos são mantidos para buscas instantâneas.
    """
    from src.utils.cache_datajud import limpar_cache_expirado

    removidos = limpar_cache_expirado()

    return {
        "status": "concluído",
        "caches_removidos": removidos,
        "mensagem": f"Removidos {removidos} caches expirados"
    }
