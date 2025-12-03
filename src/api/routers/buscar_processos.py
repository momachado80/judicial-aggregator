from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.utils.comarcas import get_comarca_nome, extrair_codigo_comarca, COMARCAS_TJSP

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

# Movimentos que indicam processo extinto/arquivado
MOVIMENTOS_EXTINTOS = {
    "Definitivo", 
    "Baixa Definitiva", 
    "Arquivado",
    "Arquivamento",
    "Trânsito em Julgado"
}


def get_codigo_comarca_por_nome(nome: str) -> Optional[str]:
    nome_lower = nome.lower().strip()
    for codigo, nome_comarca in COMARCAS_TJSP.items():
        if nome_lower == nome_comarca.lower():
            return codigo
    for codigo, nome_comarca in COMARCAS_TJSP.items():
        if nome_lower in nome_comarca.lower():
            return codigo
    return None


def get_ultimo_movimento(movimentos: List[Dict]) -> Dict:
    """Retorna o movimento mais recente ordenando por data"""
    if not movimentos:
        return {}
    
    # Ordenar por dataHora (mais recente primeiro)
    movs_ordenados = sorted(
        movimentos, 
        key=lambda m: m.get("dataHora", ""), 
        reverse=True
    )
    return movs_ordenados[0] if movs_ordenados else {}


def processo_esta_ativo(movimentos: List[Dict]) -> bool:
    """Verifica se processo está ativo baseado no movimento MAIS RECENTE"""
    ultimo = get_ultimo_movimento(movimentos)
    if not ultimo:
        return True  # Sem movimentos = assumir ativo
    
    nome_mov = ultimo.get("nome", "")
    # Verificar se contém algum termo de extinção
    for termo in MOVIMENTOS_EXTINTOS:
        if termo.lower() in nome_mov.lower():
            return False
    return True


def _buscar_sync(tribunal: str, tipo: str, codigo_comarca: Optional[str], quantidade: int) -> List[Dict]:
    """Busca síncrona para usar com ThreadPoolExecutor"""
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
            ativo = processo_esta_ativo(movimentos)
            
            processos.append({
                "numero": numero,
                "tribunal": tribunal,
                "tipo": tipo,
                "comarca": get_comarca_nome(codigo, tribunal),
                "codigo_comarca": codigo,
                "data_ajuizamento": source.get("dataAjuizamento"),
                "ultimo_movimento": ultimo_mov.get("nome", ""),
                "data_ultimo_movimento": ultimo_mov.get("dataHora", "")[:10] if ultimo_mov.get("dataHora") else "",
                "ativo": ativo,
                "url_tjsp": f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&dadosConsulta.valorConsultaNuUnificado={numero[:7]}-{numero[7:9]}.{numero[9:13]}.{numero[13:14]}.{numero[14:16]}.{numero[16:20]}"
            })
        
        return processos
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []


@router.post("/buscar-processos")
async def buscar_processos(request: BuscarProcessosRequest):
    """Busca processos em paralelo"""
    try:
        loop = asyncio.get_event_loop()
        tasks = []
        
        codigos_comarca = []
        if request.comarcas:
            for nome in request.comarcas:
                codigo = get_codigo_comarca_por_nome(nome)
                if codigo:
                    codigos_comarca.append(codigo)
        
        if codigos_comarca:
            for codigo in codigos_comarca:
                for tribunal in request.tribunais:
                    for tipo in request.tipos_processo:
                        task = loop.run_in_executor(
                            executor, _buscar_sync, 
                            tribunal, tipo, codigo, request.quantidade
                        )
                        tasks.append(task)
        else:
            for tribunal in request.tribunais:
                for tipo in request.tipos_processo:
                    task = loop.run_in_executor(
                        executor, _buscar_sync,
                        tribunal, tipo, None,
                        request.quantidade // len(request.tipos_processo)
                    )
                    tasks.append(task)
        
        resultados = await asyncio.gather(*tasks)
        
        todos = []
        for r in resultados:
            todos.extend(r)
        
        # Filtrar extintos (agora com ordenação correta por data!)
        if not request.incluir_extintos:
            ativos = [p for p in todos if p.get("ativo", True)]
            print(f"📊 Total: {len(todos)} | Ativos: {len(ativos)} | Extintos filtrados: {len(todos) - len(ativos)}")
            todos = ativos
        
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
