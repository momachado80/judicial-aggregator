from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Literal
import requests
from src.database import get_db
from src.models import Processo
from sqlalchemy.exc import IntegrityError

router = APIRouter()

class BuscaProcessosRequest(BaseModel):
    tribunal: Literal["TJSP", "TJBA"]
    tipo_processo: Literal["Inventário", "Divórcio Litigioso", "Divórcio Consensual"]
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
    
    if request.valor_causa_min or request.valor_causa_max:
        range_filter = {}
        if request.valor_causa_min:
            range_filter["gte"] = request.valor_causa_min
        if request.valor_causa_max:
            range_filter["lte"] = request.valor_causa_max
        must_clauses.append({"range": {"valorCausa": range_filter}})
    
    payload = {
        "query": {"bool": {"must": must_clauses}},
        "size": min(request.limit, 1000),
        "sort": [{"dataAjuizamento": {"order": "desc"}}]
    }
    
    try:
        response = requests.post(urls[request.tribunal], json=payload, headers=headers, timeout=30)
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        processos_salvos = []
        stats = {"novos": 0, "duplicados": 0, "inativos": 0}
        
        for hit in hits:
            source = hit.get("_source", {})
            numero = source.get("numeroProcesso", "")
            movimentos = source.get("movimentos", [])
            
            if not numero or not processo_esta_ativo(movimentos):
                stats["inativos"] += 1
                continue
            
            existe = db.query(Processo).filter(Processo.numero_processo == numero).first()
            
            if existe:
                stats["duplicados"] += 1
                processos_salvos.append({"id": existe.id, "numero_cnj": existe.numero_processo, "novo": False})
                continue
            
            processo = Processo(
                numero_processo=numero,
                tribunal=request.tribunal,
                tipo_processo=request.tipo_processo,
                classe=request.tipo_processo,
                comarca="A definir",
                valor_causa=source.get("valorCausa"),
                relevancia="Alta",
                status="pendente"
            )
            
            db.add(processo)
            db.flush()
            stats["novos"] += 1
            processos_salvos.append({"id": processo.id, "numero_cnj": processo.numero_processo, "novo": True})
        
        db.commit()
        return {"success": True, "stats": stats, "processos": processos_salvos}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
