from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import requests
from src.utils.comarcas import get_comarca_nome, extrair_codigo_comarca, COMARCAS_TJSP

router = APIRouter()

class BuscarProcessosRequest(BaseModel):
    tribunais: List[str]
    tipos_processo: List[str]
    comarcas: Optional[List[str]] = None
    quantidade: int = 100
    usar_cache: bool = True
    incluir_extintos: bool = False  # Por padrão, exclui extintos

TIPOS_PROCESSO_MAPPING = {
    "Inventário": 39,
    "Divórcio Litigioso": 12541,
    "Divórcio Consensual": 12372
}

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

# Movimentos que indicam processo extinto/arquivado
MOVIMENTOS_EXTINTOS = {"Definitivo", "Arquivado", "Baixa Definitiva", "Trânsito em Julgado"}


def get_codigo_comarca_por_nome(nome: str) -> Optional[str]:
    nome_lower = nome.lower().strip()
    for codigo, nome_comarca in COMARCAS_TJSP.items():
        if nome_lower == nome_comarca.lower():
            return codigo
    for codigo, nome_comarca in COMARCAS_TJSP.items():
        if nome_lower in nome_comarca.lower() or nome_comarca.lower() in nome_lower:
            return codigo
    return None


def processo_esta_ativo(movimentos: List[Dict]) -> bool:
    """Verifica se processo está ativo baseado no último movimento"""
    if not movimentos:
        return True  # Sem movimentos = assumir ativo
    ultimo = movimentos[-1]
    nome_mov = ultimo.get("nome", "")
    return nome_mov not in MOVIMENTOS_EXTINTOS


def extrair_dados_processo(source: Dict, tribunal: str, tipo: str) -> Optional[Dict]:
    """Extrai dados do processo do resultado da API"""
    numero = source.get("numeroProcesso", "")
    if not numero:
        return None
    
    movimentos = source.get("movimentos", [])
    ultimo_mov = movimentos[-1] if movimentos else {}
    
    codigo = extrair_codigo_comarca(numero)
    nome_comarca = get_comarca_nome(codigo, tribunal)
    
    return {
        "numero": numero,
        "tribunal": tribunal,
        "tipo": tipo,
        "comarca": nome_comarca,
        "codigo_comarca": codigo,
        "valor_causa": source.get("valorCausa"),
        "data_ajuizamento": source.get("dataAjuizamento"),
        "ultimo_movimento": ultimo_mov.get("nome", ""),
        "ativo": processo_esta_ativo(movimentos),
        "total_movimentos": len(movimentos),
        "url_tjsp": f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&dadosConsulta.valorConsultaNuUnificado={numero[:7]}-{numero[7:9]}.{numero[9:13]}.{numero[13:14]}.{numero[14:16]}.{numero[16:20]}"
    }


async def _buscar_api_cnj(tribunal: str, tipo: str, codigo_comarca: Optional[str], quantidade: int) -> List[Dict]:
    """Busca processos na API DataJud"""
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
        response = requests.post(url, headers=headers, json=query, timeout=60)
        if response.status_code != 200:
            print(f"❌ Erro API: {response.status_code}")
            return []
        
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        processos = []
        for hit in hits:
            proc = extrair_dados_processo(hit.get("_source", {}), tribunal, tipo)
            if proc:
                processos.append(proc)
        
        return processos
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []


@router.post("/buscar-processos")
async def buscar_processos(request: BuscarProcessosRequest):
    """Busca processos na API DataJud"""
    try:
        todos_processos = []
        qtd_por_tipo = max(request.quantidade // len(request.tipos_processo), 100)
        
        if request.comarcas and len(request.comarcas) > 0:
            for comarca_nome in request.comarcas:
                codigo = get_codigo_comarca_por_nome(comarca_nome)
                if not codigo:
                    print(f"⚠️ Comarca não encontrada: {comarca_nome}")
                    continue
                
                for tribunal in request.tribunais:
                    for tipo in request.tipos_processo:
                        # Buscar mais para compensar os extintos que serão filtrados
                        processos = await _buscar_api_cnj(tribunal, tipo, codigo, qtd_por_tipo * 3)
                        todos_processos.extend(processos)
        else:
            for tribunal in request.tribunais:
                for tipo in request.tipos_processo:
                    processos = await _buscar_api_cnj(tribunal, tipo, None, qtd_por_tipo)
                    todos_processos.extend(processos)
        
        # Filtrar extintos se necessário
        if not request.incluir_extintos:
            antes = len(todos_processos)
            todos_processos = [p for p in todos_processos if p.get("ativo", True)]
            print(f"📊 Filtrados {antes - len(todos_processos)} processos extintos")
        
        # Remover duplicados
        vistos = set()
        unicos = []
        for p in todos_processos:
            if p["numero"] not in vistos:
                vistos.add(p["numero"])
                unicos.append(p)
        
        # Ordenar por data
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
