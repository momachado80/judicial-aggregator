from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database import get_db
from src.models import Processo

router = APIRouter()

@router.get("")
def list_processes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tribunal: str = None,
    tipo_processo: str = None,
    relevancia: str = None,
    db: Session = Depends(get_db)
):
    """Lista processos com filtros opcionais"""
    query = db.query(Processo)
    
    if tribunal:
        query = query.filter(Processo.tribunal == tribunal)
    if tipo_processo:
        query = query.filter(Processo.tipo_processo == tipo_processo)
    if relevancia:
        query = query.filter(Processo.relevancia == relevancia)
    
    total = query.count()
    skip = (page - 1) * page_size
    processos = query.order_by(Processo.created_at.desc()).offset(skip).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "items": [
            {
                "id": p.id,
                "numero_cnj": p.numero_processo,
                "tribunal": p.tribunal,
                "tipo_processo": p.tipo_processo,
                "classe": p.classe,
                "comarca": p.comarca,
                "relevance": p.relevancia,
                "score_relevancia": p.score_relevancia,
                "data_ajuizamento": p.data_ajuizamento.isoformat() if p.data_ajuizamento else None,
                "valor_causa": p.valor_causa,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in processos
        ]
    }

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Estatísticas dos processos"""
    
    # Por tribunal
    por_tribunal = db.query(
        Processo.tribunal,
        func.count(Processo.id).label('count')
    ).group_by(Processo.tribunal).all()
    
    # Por relevância
    por_relevancia = db.query(
        Processo.relevancia,
        func.count(Processo.id).label('count')
    ).group_by(Processo.relevancia).all()
    
    # Por tipo
    por_tipo = db.query(
        Processo.tipo_processo,
        func.count(Processo.id).label('count')
    ).group_by(Processo.tipo_processo).all()
    
    return {
        "por_tribunal": dict(por_tribunal),
        "por_relevancia": dict(por_relevancia),
        "por_tipo": dict(por_tipo),
        "total": db.query(func.count(Processo.id)).scalar()
    }

@router.get("/{process_id}")
def get_process(process_id: int, db: Session = Depends(get_db)):
    """Buscar processo por ID"""
    processo = db.query(Processo).filter(Processo.id == process_id).first()
    if not processo:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    
    return {
        "id": processo.id,
        "numero_cnj": processo.numero_processo,
        "tribunal": processo.tribunal,
        "tipo_processo": processo.tipo_processo,
        "classe": processo.classe,
        "comarca": processo.comarca,
        "relevance": processo.relevancia,
        "score_relevancia": processo.score_relevancia,
        "data_ajuizamento": processo.data_ajuizamento.isoformat() if processo.data_ajuizamento else None,
        "valor_causa": processo.valor_causa,
        "created_at": processo.created_at.isoformat() if processo.created_at else None,
        "updated_at": processo.updated_at.isoformat() if processo.updated_at else None,
    }
