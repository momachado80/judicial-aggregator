from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.utils.comarcas import get_comarca_nome, extrair_codigo_comarca, COMARCAS_TJSP, expandir_sao_paulo, FOROS_SAO_PAULO_CAPITAL

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=10)

class BuscarProcessosRequest(BaseModel):
    tribunais: List[str]
    tipos_processo: List[str]
    comarcas: Optional[List[str]] = None
    quantidade: int = 500
    usar_cache: bool = True
    incluir_extintos: bool = False

TIPOS_PROCESSO_MAPPING = {
    "Inventário": 39,
    "Divórcio Litigioso": 12541,
    "Divórcio Consensual": 12372
}

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

MOVIMENTOS_INATIVOS = {
    "baixa definitiva",
    "arquivado definitivamente",
    "trânsito em julgado",
    "processo suspenso",
    "suspensão do processo",
    "sobrestamento",
}


def get_codigos_comarca_por_nome(nome: str) -> List[str]:
    nome_lower = nome.lower().strip()
    
    if nome_lower in ["são paulo", "sao paulo", "sp capital", "são paulo (capital)", "sao paulo (capital)", "capital"]:
        return list(FOROS_SAO_PAULO_CAPITAL)
    
    for codigo, nome_comarca in COMARCAS_TJSP.items():
        if nome_lower == nome_comarca.lower():
            return [codigo]
    
    for codigo, nome_comarca in COMARCAS_TJSP.items():
        if nome_lower in nome_comarca.lower() or nome_comarca.lower() in nome_lower:
            return [codigo]
    
    return []


def get_ultimo_movimento(movimentos: List[Dict]) -> Dict:
    if not movimentos:
        return {}
    movs_ordenados = sorted(movimentos, key=lambda m: m.get("dataHora", ""), reverse=True)
    return movs_ordenados[0] if movs_ordenados else {}


def processo_esta_ativo(movimentos: List[Dict]) -> tuple[bool, str]:
    ultimo = get_ultimo_movimento(movimentos)
    if not ultimo:
        return True, "sem_movimentos"
    
    nome_mov = ultimo.get("nome", "").lower().strip()
    
    if nome_mov == "definitivo":
        return False, "definitivo"
    
    for termo in MOVIMENTOS_INATIVOS:
        if termo in nome_mov:
            return False, termo
    
    return True, "ativo"


def _buscar_sync(tribunal: str, tipo: str, codigo_comarca: Optional[str], quantidade: int, search_after: Optional[List] = None) -> tuple[List[Dict], Optional[List]]:
    """Busca processos com suporte a paginação via search_after"""
    tipo_cod = TIPOS_PROCESSO_MAPPING.get(tipo, 39)
    url = f"https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal.lower()}/_search"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"APIKey {DATAJUD_API_KEY}"
    }
    
    must_clauses = [{"term": {"classe.codigo": tipo_cod}}]
    
    query = {
        "query": {"bool": {"must": must_clauses}},
        "size": 1000,
        "sort": [{"dataAjuizamento": {"order": "desc"}}, {"numeroProcesso": {"order": "desc"}}]
    }
    
    if search_after:
        query["search_after"] = search_after
    
    try:
        response = requests.post(url, headers=headers, json=query, timeout=60)
        if response.status_code != 200:
            return [], None
        
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        if not hits:
            return [], None
        
        last_sort = hits[-1].get("sort") if hits else None
        
        processos = []
        for hit in hits:
            source = hit.get("_source", {})
            numero = source.get("numeroProcesso", "")
            if not numero:
                continue
            
            codigo = extrair_codigo_comarca(numero)
            
            if codigo_comarca and codigo != codigo_comarca:
                continue
            
            movimentos = source.get("movimentos", [])
            ultimo_mov = get_ultimo_movimento(movimentos)
            ativo, motivo = processo_esta_ativo(movimentos)
            
            processos.append({
                "numero": numero,
                "tribunal": tribunal,
                "tipo": tipo,
                "comarca": get_comarca_nome(codigo, tribunal),
                "codigo_comarca": codigo,
                "data_ajuizamento": source.get("dataAjuizamento"),
                "valor_causa": source.get("valorCausa"),
                "ultimo_movimento": ultimo_mov.get("nome", ""),
                "data_ultimo_movimento": ultimo_mov.get("dataHora", "")[:10] if ultimo_mov.get("dataHora") else "",
                "ativo": ativo,
                "motivo_inativo": motivo if not ativo else None,
                "url_tjsp": f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&dadosConsulta.valorConsultaNuUnificado={numero[:7]}-{numero[7:9]}.{numero[9:13]}.{numero[13:14]}.{numero[14:16]}.{numero[16:20]}"
            })
        
        return processos, last_sort
    except Exception as e:
        print(f"Erro busca {tipo}: {e}")
        return [], None


def _buscar_com_paginacao(tribunal: str, tipo: str, codigo_comarca: Optional[str], max_processos: int) -> List[Dict]:
    """Busca com paginação para coletar mais processos de uma comarca específica"""
    todos_processos = []
    search_after = None
    max_paginas = 20 if codigo_comarca else 1
    
    for pagina in range(max_paginas):
        processos, search_after = _buscar_sync(tribunal, tipo, codigo_comarca, 1000, search_after)
        todos_processos.extend(processos)
        
        print(f"Pagina {pagina+1}: encontrados {len(processos)} processos, total: {len(todos_processos)}")
        
        if len(todos_processos) >= max_processos:
            break
        
        if not search_after or len(processos) == 0:
            break
    
    return todos_processos[:max_processos]


@router.post("/buscar-processos")
async def buscar_processos(request: BuscarProcessosRequest):
    try:
        loop = asyncio.get_event_loop()
        tasks = []
        
        max_por_busca = request.quantidade if request.comarcas else 1000
        
        codigos_comarca = []
        if request.comarcas:
            for nome in request.comarcas:
                codigos = get_codigos_comarca_por_nome(nome)
                codigos_comarca.extend(codigos)
        
        if codigos_comarca:
            for codigo in codigos_comarca:
                for tribunal in request.tribunais:
                    for tipo in request.tipos_processo:
                        task = loop.run_in_executor(
                            executor, _buscar_com_paginacao, 
                            tribunal, tipo, codigo, max_por_busca
                        )
                        tasks.append(task)
        else:
            for tribunal in request.tribunais:
                for tipo in request.tipos_processo:
                    task = loop.run_in_executor(
                        executor, _buscar_com_paginacao,
                        tribunal, tipo, None, 1000
                    )
                    tasks.append(task)
        
        resultados = await asyncio.gather(*tasks)
        
        todos = []
        for r in resultados:
            todos.extend(r)
        
        if not request.incluir_extintos:
            antes = len(todos)
            todos = [p for p in todos if p.get("ativo", True)]
            filtrados = antes - len(todos)
            print(f"Total: {antes} | Ativos: {len(todos)} | Extintos removidos: {filtrados}")
        
        vistos = set()
        unicos = []
        for p in todos:
            if p["numero"] not in vistos:
                vistos.add(p["numero"])
                unicos.append(p)
        
        unicos.sort(key=lambda x: x.get("data_ajuizamento", ""), reverse=True)
        
        return unicos[:request.quantidade]
        
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comarcas")
async def listar_comarcas():
    from src.utils.comarcas import COMARCAS_TJSP, COMARCAS_TJBA
    return {
        "TJSP": sorted(set(COMARCAS_TJSP.values())),
        "TJBA": sorted(set(COMARCAS_TJBA.values()))
    }
