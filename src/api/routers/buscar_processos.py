from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import requests
from datetime import datetime
from src.utils.comarcas import get_nome_comarca, extrair_codigo_comarca

router = APIRouter()

class BuscarProcessosRequest(BaseModel):
    tribunais: List[str]
    tipos_processo: List[str]
    comarcas: Optional[List[str]] = None
    valor_causa_min: Optional[float] = None
    valor_causa_max: Optional[float] = None
    ano: Optional[int] = None
    quantidade: int = 50

TRIBUNAL_SIGLAS = {
    "TJSP": "8.26",
    "TJBA": "8.20"
}

TIPOS_PROCESSO_MAPPING = {
    "Inventário": "289",
    "Divórcio Litigioso": "1107", 
    "Divórcio Consensual": "1108"
}

@router.post("/buscar-processos")
async def buscar_processos(request: BuscarProcessosRequest):
    """
    Busca processos judiciais ativos na API DataJud
    """
    try:
        todos_processos = []
        
        for tribunal in request.tribunais:
            for tipo in request.tipos_processo:
                # Montar query
                tribunal_cod = TRIBUNAL_SIGLAS.get(tribunal, "8.26")
                tipo_cod = TIPOS_PROCESSO_MAPPING.get(tipo, "289")
                
                # Calcular quantidade por combinação
                quantidade_por_busca = max(10, request.quantidade * 10)
                
                # Buscar na API DataJud
                url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
                
                query = {
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"siglaTribunal": tribunal}},
                                {"term": {"classe.codigo": tipo_cod}},
                                {"term": {"grau": "1"}},
                                {"range": {"movimentos.dataHora": {"gte": "now-90d"}}}
                            ],
                            "must_not": [
                                {"terms": {"movimentos.nome.keyword": [
                                    "Arquivamento Definitivo",
                                    "Processo Extinto",
                                    "Baixa Definitiva",
                                    "Remetido ao Arquivo"
                                ]}}
                            ]
                        }
                    },
                    "size": quantidade_por_busca,
                    "sort": [{"dataAjuizamento": {"order": "desc"}}]
                }
                
                response = requests.post(url, json=query, timeout=30)
                
                if response.status_code != 200:
                    continue
                    
                data = response.json()
                hits = data.get("hits", {}).get("hits", [])
                
                for hit in hits:
                    source = hit.get("_source", {})
                    numero = source.get("numeroProcesso", "")
                    
                    # Extrair código da comarca do número do processo
                    codigo_comarca = extrair_codigo_comarca(numero)
                    
                    # Obter nome da comarca
                    nome_comarca = get_nome_comarca(codigo_comarca, tribunal)
                    
                    # Se tem filtro de comarca, verificar
                    if request.comarcas:
                        # Filtrar por nome ou código
                        comarca_match = any(
                            c.lower() in nome_comarca.lower() or 
                            c == codigo_comarca
                            for c in request.comarcas
                        )
                        if not comarca_match:
                            continue
                    
                    # Filtrar por valor
                    valor_causa = source.get("valorCausa")
                    if request.valor_causa_min and valor_causa:
                        if valor_causa < request.valor_causa_min:
                            continue
                    if request.valor_causa_max and valor_causa:
                        if valor_causa > request.valor_causa_max:
                            continue
                    
                    # Filtrar por ano
                    if request.ano:
                        data_ajuiz = source.get("dataAjuizamento", "")
                        if data_ajuiz and not data_ajuiz.startswith(str(request.ano)):
                            continue
                    
                    processo = {
                        "numero": numero,
                        "tribunal": tribunal,
                        "tipo": tipo,
                        "comarca": nome_comarca,
                        "valor_causa": valor_causa,
                        "data_ajuizamento": source.get("dataAjuizamento"),
                        "url_tjsp": f"https://esaj.tjsp.jus.br/cpopg/show.do?processo.numero={numero}" if tribunal == "TJSP" else None
                    }
                    
                    todos_processos.append(processo)
                    
                    # Parar quando atingir quantidade desejada
                    if len(todos_processos) >= request.quantidade:
                        break
                
                if len(todos_processos) >= request.quantidade:
                    break
            
            if len(todos_processos) >= request.quantidade:
                break
        
        # Limitar ao número solicitado
        todos_processos = todos_processos[:request.quantidade]
        
        return todos_processos
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
