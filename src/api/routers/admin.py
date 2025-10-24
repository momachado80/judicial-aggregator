from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.database import get_db
from src.normalization.models import Movement, Process
router = APIRouter()
@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_processes = db.query(func.count(Process.id)).scalar()
    total_movements = db.query(func.count(Movement.id)).scalar()
    by_tribunal = db.query(Process.tribunal, func.count(Process.id).label("count")).group_by(Process.tribunal).all()
    by_relevance = db.query(Process.relevance, func.count(Process.id).label("count")).group_by(Process.relevance).all()
    latest = db.query(Process).order_by(Process.updated_at.desc()).first()
    return {"total_processes": total_processes, "total_movements": total_movements, "by_tribunal": [{"tribunal": t, "count": c} for t, c in by_tribunal], "by_relevance": [{"relevance": r, "count": c} for r, c in by_relevance], "latest_update": latest.updated_at if latest else None}
