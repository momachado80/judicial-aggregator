from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from src.database import get_db
from src.normalization.models import Process

router = APIRouter()

@router.get("/stats")
def get_statistics(db: Session = Depends(get_db)):
    por_tribunal = db.query(
        Process.tribunal,
        func.count(Process.id).label('total')
    ).group_by(Process.tribunal).all()
    
    por_relevancia = db.query(
        Process.relevance,
        func.count(Process.id).label('total')
    ).group_by(Process.relevance).all()
    
    por_classe = db.query(
        Process.classe_tpu,
        func.count(Process.id).label('total')
    ).group_by(Process.classe_tpu).all()
    
    por_mes = db.query(
        extract('year', Process.created_at).label('ano'),
        extract('month', Process.created_at).label('mes'),
        func.count(Process.id).label('total')
    ).group_by('ano', 'mes').order_by('ano', 'mes').all()
    
    valor_por_tribunal = db.query(
        Process.tribunal,
        func.sum(Process.valor_causa).label('valor_total')
    ).group_by(Process.tribunal).all()
    
    return {
        "por_tribunal": [{"tribunal": t, "total": c} for t, c in por_tribunal],
        "por_relevancia": [{"relevancia": r, "total": c} for r, c in por_relevancia],
        "por_classe": [
            {"classe": "Divórcio" if c == "8015" else "Inventário", "total": cnt} 
            for c, cnt in por_classe
        ],
        "por_mes": [{"mes": f"{int(m):02d}/{int(a)}", "total": c} for a, m, c in por_mes],
        "valor_por_tribunal": [{"tribunal": t, "valor": float(v) if v else 0} for t, v in valor_por_tribunal],
        "total_geral": db.query(func.count(Process.id)).scalar(),
        "valor_total": float(db.query(func.sum(Process.valor_causa)).scalar() or 0)
    }
