from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Literal, List
import requests
from src.database import get_db
from src.models import Processo
from sqlalchemy.exc import IntegrityError

router = APIRouter()

class BuscaProcessosRequest(BaseModel):
    tribunal: Literal["TJSP", "TJBA"]
    tipo_processo: Literal["Inventário", "Divórcio Litigioso", "Divórcio Consensual"]
    comarcas: Optional[List[str]] = None
    valor_causa_min: Optional[float] = None
    valor_causa_max: Optional[float] = None
    limit: int = 500

PALAVRAS_FINALIZACAO = [
    "sentença extintiva", "processo extinto", "extinção",
    "arquivamento", "arquivado", "homologação da partilha",
    "partilha homologada", "trânsito em julgado", "suspenso"
]

def processo_esta_ativo(movimentos):
    if not movimentos:
        return True
    ultimas = movimentos[-15:] if len(movimentos) > 15 else movimentos
    texto = " ".join([m.get("nome", "").lower() for m in ultimas])
    return not any(palavra in texto for palavra in PALAVRAS_FINALIZACAO)

@router.post("")
def buscar_processos(request: BuscaProcessosRequest, db: Session = Depends(get_db)):
    urls = {
        "TJSP": "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search",
        "TJBA": "https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search"
    }
    
    headers = {
        "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
    }
    
    must_clauses = [{"match": {"classe.nome": request.tipo_processo}}]
    
    # Adicionar filtro de comarcas se fornecido
    if request.comarcas and len(request.comarcas) > 0:
        should_comarcas = []
        for comarca in request.comarcas:
            should_comarcas.append({"match": {"orgaoJulgador.comarca": comarca}})
        must_clauses.append({"bool": {"should": should_comarcas, "minimum_should_match": 1}})
    
    if request.valor_causa_min or request.valor_causa_max:
        range_filter = {}
        if request.valor_causa_min:
            range_filter["gte"] = request.valor_causa_min
        if request.valor_causa_max:
            range_filter["lte"] = request.valor_causa_max
        must_clauses.append({"range": {"valorCausa": range_filter}})
    
    query = {
        "size": request.limit,
        "query": {"bool": {"must": must_clauses}},
        "sort": [{"dataAjuizamento": {"order": "desc"}}]
    }
    
    try:
        response = requests.post(
            urls[request.tribunal],
            headers=headers,
            json=query,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        processos_encontrados = []
        novos = 0
        duplicados = 0
        inativos = 0
        
        for hit in data.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            numero_cnj = source.get("numeroProcesso")
            
            if not numero_cnj:
                continue
            
            movimentos = source.get("movimentos", [])
            if not processo_esta_ativo(movimentos):
                inativos += 1
                continue
            
            processo_existente = db.query(Processo).filter(
                Processo.numero_cnj == numero_cnj
            ).first()
            
            comarca = source.get("orgaoJulgador", {}).get("comarca", "")
            tipo_processo = source.get("classe", {}).get("nome", "")
            valor_causa = source.get("valorCausa")
            data_ajuizamento = source.get("dataAjuizamento")
            
            if processo_existente:
                duplicados += 1
                processos_encontrados.append({
                    "id": processo_existente.id,
                    "numero_cnj": numero_cnj,
                    "tribunal": request.tribunal,
                    "tipo_processo": tipo_processo,
                    "comarca": comarca,
                    "valor_causa": valor_causa,
                    "data_ajuizamento": data_ajuizamento,
                    "novo": False
                })
            else:
                try:
                    novo_processo = Processo(
                        numero_cnj=numero_cnj,
                        tribunal=request.tribunal,
                        tipo_processo=tipo_processo,
                        comarca=comarca,
                        valor_causa=valor_causa,
                        data_ajuizamento=data_ajuizamento,
                        classe=source.get("classe", {}).get("codigo", ""),
                        relevance="alta"
                    )
                    db.add(novo_processo)
                    db.commit()
                    db.refresh(novo_processo)
                    
                    novos += 1
                    processos_encontrados.append({
                        "id": novo_processo.id,
                        "numero_cnj": numero_cnj,
                        "tribunal": request.tribunal,
                        "tipo_processo": tipo_processo,
                        "comarca": comarca,
                        "valor_causa": valor_causa,
                        "data_ajuizamento": data_ajuizamento,
                        "novo": True
                    })
                except IntegrityError:
                    db.rollback()
                    duplicados += 1
        
        return {
            "success": True,
            "stats": {
                "novos": novos,
                "duplicados": duplicados,
                "inativos": inativos
            },
            "processos": processos_encontrados
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
