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
    quantidade: int = 100
    usar_cache: bool = True
    incluir_extintos: bool = False

TIPOS_PROCESSO_MAPPING = {
    "Inventário": 39,
    "Divórcio Litigioso": 12541,
    "Divórcio Consensual": 12372
}

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

# Movimentos que DEFINITIVAMENTE indicam processo encerrado
MOVIMENTOS_ENCERRADOS = {
    "baixa definitiva",
    "arquivado definitivamente",
    "trânsito em julgado",
}


def get_codigos_comarca_por_nome(nome: str) -> List[str]:
    """Retorna lista de códigos de comarca. Para São Paulo, retorna todos os foros da capital."""
    nome_lower = nome.lower().strip()
    
    # Caso especial: São Paulo Capital
    if nome_lower in ["são paulo", "sao paulo", "sp capital", "são paulo (capital)", "sao paulo (capital)", "capital"]:
        return list(FOROS_SAO_PAULO_CAPITAL)
    
    # Busca exata
    for codigo, nome_comarca in COMARCAS_TJSP.items():
        if nome_lower == nome_comarca.lower():
            return [codigo]
    
    # Busca parcial
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
    """
    Verifica se processo está ativo.
    Retorna (ativo, motivo)
    """
    ultimo = get_ultimo_movimento(movimentos)
    if not ultimo:
        return True, "sem_movimentos"
    
    nome_mov = ultimo.get("nome", "").lower().strip()
    
    # Verificar movimento "Definitivo" isolado (indica arquivamento definitivo)
    if nome_mov == "definitivo":
        return False, "definitivo"
    
    # Verificar termos específicos de encerramento
    for termo in MOVIMENTOS_ENCERRADOS:
        if termo in nome_mov:
            return False, termo
    
    return True, "ativo"


def _buscar_sync(tribunal: str, tipo: str, codigo_comarca: Optional[str], quantidade: int) -> List[Dict]:
    tipo_cod = TIPOS_PROCESSO_MAPPING.get(tipo, 39)
    url = f"https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal.lower()}/_search"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"APIKey {DATAJUD_API_KEY}"
    }
    
    must_clauses = [{"term": {"classe.codigo": tipo_cod}}]
    if codigo_comarca:
        must_clauses.append({"wildcard": {"numeroProcesso": f"*{codigo_comarca}"}})
    
    query = {
        "query": {"bool": {"must": must_clauses}},
        "size": min(quantidade, 1000),
        "sort": [{"dataAjuizamento": {"order": "desc"}}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=query, timeout=30)
        if response.status_code != 200:
            return []
        
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        processos = []
        for hit in hits:
            source = hit.get("_source", {})
            numero = source.get("numeroProcesso", "")
            if not numero:
                continue
            
            movimentos = source.get("movimentos", [])
            ultimo_mov = get_ultimo_movimento(movimentos)
            codigo = extrair_codigo_comarca(numero)
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
        
        return processos
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []


@router.post("/buscar-processos")
async def buscar_processos(request: BuscarProcessosRequest):
    try:
        loop = asyncio.get_event_loop()
        tasks = []
        
        qtd_por_busca = 1000
        
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
                            executor, _buscar_sync, 
                            tribunal, tipo, codigo, qtd_por_busca
                        )
                        tasks.append(task)
        else:
            for tribunal in request.tribunais:
                for tipo in request.tipos_processo:
                    task = loop.run_in_executor(
                        executor, _buscar_sync,
                        tribunal, tipo, None, qtd_por_busca
                    )
                    tasks.append(task)
        
        resultados = await asyncio.gather(*tasks)
        
        todos = []
        for r in resultados:
            todos.extend(r)
        
        if not request.incluir_extintos:
            antes = len(todos)
            todos = [p for p in todos if p.get("ativo", True)]
            print(f"📊 Total: {antes} | Ativos: {len(todos)} | Filtrados: {antes - len(todos)}")
        
        # Remover duplicados
        vistos = set()
        unicos = []
        for p in todos:
            if p["numero"] not in vistos:
                vistos.add(p["numero"])
                unicos.append(p)
        
        unicos.sort(key=lambda x: x.get("data_ajuizamento", ""), reverse=True)
        
        return unicos[:request.quantidade]
        
    except Exception as e:
        print(f"💥 ERRO: {e}")
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
