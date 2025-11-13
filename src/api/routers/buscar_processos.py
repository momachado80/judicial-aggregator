"""
Router para busca de processos sob demanda na API DataJud do CNJ.
VERSÃO COM FILTRO DE COMARCA NO BACKEND (após buscar da API)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx

# Import sem 'src.'
try:
    from comarca_codes import build_processo_pattern, get_comarca_code, get_all_comarcas
except ImportError:
    from src.comarca_codes import build_processo_pattern, get_comarca_code, get_all_comarcas

router = APIRouter()

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
DATAJUD_URLS = {
    "TJSP": "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search",
    "TJBA": "https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search"
}


class BuscarProcessosRequest(BaseModel):
    tribunais: List[str] = ["TJSP"]
    tipos_processo: List[str] = ["Inventário"]
    comarcas: Optional[List[str]] = None
    valor_min: Optional[float] = None
    valor_max: Optional[float] = None
    ano_ajuizamento: Optional[int] = None
    quantidade: int = 50


class ProcessoResponse(BaseModel):
    numero: str
    tribunal: str
    tipo: str
    comarca: Optional[str]
    valor_causa: Optional[float]
    data_ajuizamento: Optional[str]
    url_tjsp: Optional[str] = None


@router.post("/api/buscar-processos", response_model=List[ProcessoResponse])
async def buscar_processos(request: BuscarProcessosRequest):
    """
    Busca processos na API DataJud do CNJ com filtros.
    ESTRATÉGIA: Busca mais processos da API e filtra comarca no backend.
    """
    
    todos_processos = []
    
    for tribunal in request.tribunais:
        if tribunal not in DATAJUD_URLS:
            continue
        
        must_clauses = []
        
        # Filtro de tipos de processo (OR entre tipos)
        if request.tipos_processo:
            tipo_clauses = [
                {"match": {"classe.nome": tipo}}
                for tipo in request.tipos_processo
            ]
            must_clauses.append({
                "bool": {"should": tipo_clauses, "minimum_should_match": 1}
            })
        
        # Filtro de valor da causa
        if request.valor_min is not None or request.valor_max is not None:
            range_filter = {}
            if request.valor_min is not None:
                range_filter["gte"] = request.valor_min
            if request.valor_max is not None:
                range_filter["lte"] = request.valor_max
            must_clauses.append({
                "range": {"valorCausa": range_filter}
            })
        
        # Filtro de ano
        if request.ano_ajuizamento:
            must_clauses.append({
                "match": {"dataAjuizamento": str(request.ano_ajuizamento)}
            })
        
        # Excluir processos extintos/suspensos
        must_not_clauses = [
            {"match": {"movimentos.nome": "Extinção"}},
            {"match": {"movimentos.nome": "Suspensão"}},
            {"match": {"movimentos.nome": "Arquivamento"}}
        ]
        
        # MUDANÇA: Se tem filtro de comarca, buscar MAIS processos para garantir quantidade
        quantidade_buscar = request.quantidade
        if request.comarcas:
            # Buscar 10x mais para ter margem após filtrar
            quantidade_buscar = min(request.quantidade * 10, 1000)
            print(f"⚠️  Filtro de comarca ativado: buscando {quantidade_buscar} processos para filtrar no backend")
        
        query = {
            "size": quantidade_buscar,
            "query": {
                "bool": {
                    "must": must_clauses,
                    "must_not": must_not_clauses
                }
            },
            "sort": [{"dataAjuizamento": {"order": "desc"}}]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    DATAJUD_URLS[tribunal],
                    headers={
                        "Authorization": f"APIKey {DATAJUD_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=query
                )
                
                if response.status_code != 200:
                    print(f"❌ Erro {tribunal}: {response.status_code}")
                    print(f"Response: {response.text[:500]}")
                    continue
                
                data = response.json()
                hits = data.get("hits", {}).get("hits", [])
                
                print(f"✅ {tribunal}: {len(hits)} processos retornados da API")
                
                # Processar e FILTRAR por comarca se necessário
                processos_filtrados = []
                
                for hit in hits:
                    source = hit.get("_source", {})
                    numero_cnj = source.get("numeroProcesso", "")
                    
                    # Extrair comarca do número CNJ
                    comarca_nome = extrair_comarca_do_numero(numero_cnj, tribunal)
                    codigo_comarca = numero_cnj[-4:] if len(numero_cnj) >= 4 else None
                    
                    # FILTRO DE COMARCA NO BACKEND
                    if request.comarcas:
                        comarca_match = False
                        for comarca_filtro in request.comarcas:
                            codigo_esperado = get_comarca_code(comarca_filtro, tribunal)
                            if codigo_esperado and codigo_comarca == codigo_esperado:
                                comarca_match = True
                                break
                        
                        # Pular se não bater com nenhuma comarca solicitada
                        if not comarca_match:
                            continue
                    
                    processo = ProcessoResponse(
                        numero=numero_cnj,
                        tribunal=tribunal,
                        tipo=source.get("classe", {}).get("nome", ""),
                        comarca=comarca_nome,
                        valor_causa=source.get("valorCausa"),
                        data_ajuizamento=source.get("dataAjuizamento"),
                        url_tjsp=f"https://esaj.tjsp.jus.br/cpopg/show.do?processo.numero={numero_cnj}" if tribunal == "TJSP" else None
                    )
                    processos_filtrados.append(processo)
                    
                    # Parar quando atingir quantidade solicitada
                    if len(processos_filtrados) >= request.quantidade:
                        break
                
                print(f"✅ {tribunal}: {len(processos_filtrados)} processos após filtro de comarca")
                todos_processos.extend(processos_filtrados)
        
        except Exception as e:
            print(f"❌ Erro ao buscar {tribunal}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Erro ao buscar processos: {str(e)}")
    
    return todos_processos[:request.quantidade]


def extrair_comarca_do_numero(numero_cnj: str, tribunal: str) -> Optional[str]:
    """Extrai o nome da comarca a partir do código OOOO no número CNJ."""
    if not numero_cnj or len(numero_cnj) < 20:
        return None
    
    try:
        codigo_comarca = numero_cnj[-4:]
        comarcas = get_all_comarcas(tribunal)
        for nome, codigo in comarcas.items():
            if codigo == codigo_comarca:
                return nome.replace(" (SP)", "").replace(" (BA)", "")
        return f"Comarca {codigo_comarca}"
    except Exception as e:
        print(f"Erro ao extrair comarca: {e}")
        return None


@router.get("/api/comarcas/{tribunal}")
async def listar_comarcas(tribunal: str):
    """Lista todas as comarcas disponíveis para um tribunal."""
    if tribunal not in ["TJSP", "TJBA"]:
        raise HTTPException(status_code=400, detail="Tribunal inválido. Use TJSP ou TJBA.")
    
    comarcas = get_all_comarcas(tribunal)
    return {
        "tribunal": tribunal,
        "total": len(comarcas),
        "comarcas": [
            {"nome": nome, "codigo": codigo}
            for nome, codigo in sorted(comarcas.items())
        ]
    }
