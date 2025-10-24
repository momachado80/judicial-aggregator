from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.database import get_db
from src.normalization.models import Process
from typing import Optional

router = APIRouter()

@router.get("")
def list_processes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    tribunal: Optional[str] = None,
    classe_tpu: Optional[str] = None,
    relevance: Optional[str] = None,
    numero_cnj: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Process)
    
    if tribunal:
        query = query.filter(Process.tribunal == tribunal)
    if classe_tpu:
        query = query.filter(Process.classe_tpu == classe_tpu)
    if relevance:
        query = query.filter(Process.relevance == relevance)
    if numero_cnj:
        query = query.filter(Process.numero_cnj.contains(numero_cnj))
    
    total = query.count()
    processes = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": processes,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/{process_id}")
def get_process(process_id: int, db: Session = Depends(get_db)):
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Process not found")
    return process
