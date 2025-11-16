from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import Optional
from datetime import date
from src.database import get_db
from src.models import Processo
from src.utils.tribunal_links import gerar_link_tribunal

router = APIRouter()

@router.get("")
def list_processes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    tribunal: Optional[str] = None,
    tipo_processo: Optional[str] = None,
    relevancia: Optional[str] = None,
    status: Optional[str] = Query(None, description="Filtrar por status"),
    data_ajuizamento_inicio: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    data_ajuizamento_fim: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)"),
    valor_causa_min: Optional[float] = Query(None, ge=0, description="Valor mínimo"),
    valor_causa_max: Optional[float] = Query(None, ge=0, description="Valor máximo"),
    comarca: Optional[str] = Query(None, description="Filtrar por comarca"),
    vara: Optional[str] = Query(None, description="Filtrar por vara"),
    numero_processo: Optional[str] = Query(None, description="Buscar por número"),
    sort_by: Optional[str] = Query("created_at", description="Ordenar por"),
    sort_order: Optional[str] = Query("desc", description="Ordem (asc/desc)"),
    db: Session = Depends(get_db)
):
    """Lista processos com filtros avançados"""
    query = db.query(Processo)
    
    if tribunal:
        query = query.filter(Processo.tribunal == tribunal)
    if tipo_processo:
        query = query.filter(Processo.tipo_processo == tipo_processo)
    if relevancia:
        query = query.filter(Processo.relevancia == relevancia)
    if status:
        query = query.filter(Processo.status == status)
    
    if data_ajuizamento_inicio:
        query = query.filter(Processo.data_ajuizamento >= data_ajuizamento_inicio)
    
    if data_ajuizamento_fim:
        query = query.filter(Processo.data_ajuizamento <= data_ajuizamento_fim)
    
    if valor_causa_min is not None:
        query = query.filter(Processo.valor_causa >= valor_causa_min)
    
    if valor_causa_max is not None:
        query = query.filter(Processo.valor_causa <= valor_causa_max)
    
    if comarca:
        query = query.filter(Processo.comarca.ilike(f"%{comarca}%"))
    
    if vara:
        query = query.filter(Processo.vara.ilike(f"%{vara}%"))
    
    if numero_processo:
        numero_limpo = numero_processo.replace("-", "").replace(".", "")
        query = query.filter(
            or_(
                Processo.numero_processo.ilike(f"%{numero_processo}%"),
                Processo.numero_processo.ilike(f"%{numero_limpo}%")
            )
        )
    
    total = query.count()
    
    if sort_by == "data_ajuizamento":
        order_col = Processo.data_ajuizamento
    elif sort_by == "valor_causa":
        order_col = Processo.valor_causa
    elif sort_by == "relevancia":
        order_col = func.case(
            (Processo.relevancia == 'alta', 3),
            (Processo.relevancia == 'media', 2),
            (Processo.relevancia == 'baixa', 1),
            else_=0
        )
    else:
        order_col = Processo.created_at
    
    if sort_order == "asc":
        query = query.order_by(order_col.asc())
    else:
        query = query.order_by(order_col.desc())
    
    skip = (page - 1) * page_size
    processos = query.offset(skip).limit(page_size).all()
    
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
                "vara": p.vara if hasattr(p, 'vara') else None,
                "relevance": p.relevancia,
                "score_relevancia": p.score_relevancia,
                "status": p.status if hasattr(p, 'status') else 'pendente',
                "data_ajuizamento": p.data_ajuizamento.isoformat() if p.data_ajuizamento else None,
                "valor_causa": float(p.valor_causa) if p.valor_causa else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                "movimentacoes": p.movimentacoes,
            }
            for p in processos
        ]
    }


@router.get("/varas")
def get_varas(
    comarca: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lista todas as varas únicas"""
    query = db.query(Processo.vara).distinct().filter(Processo.vara.isnot(None))
    
    if comarca:
        query = query.filter(Processo.comarca.ilike(f"%{comarca}%"))
    
    varas = query.all()
    return {
        "varas": sorted([v[0] for v in varas if v[0]])
    }

@router.get("/stats/filters")
def get_filter_stats(db: Session = Depends(get_db)):
    """Estatísticas para ajudar nos filtros"""
    stats = {
        "data_ajuizamento": {
            "min": db.query(func.min(Processo.data_ajuizamento)).scalar(),
            "max": db.query(func.max(Processo.data_ajuizamento)).scalar()
        },
        "valor_causa": {
            "min": float(db.query(func.min(Processo.valor_causa)).scalar() or 0),
            "max": float(db.query(func.max(Processo.valor_causa)).scalar() or 0)
        },
        "totais": {
            "comarcas": db.query(func.count(func.distinct(Processo.comarca))).scalar(),
            "varas": db.query(func.count(func.distinct(Processo.vara))).scalar()
        }
    }
    
    if stats["data_ajuizamento"]["min"]:
        stats["data_ajuizamento"]["min"] = stats["data_ajuizamento"]["min"].isoformat()
    if stats["data_ajuizamento"]["max"]:
        stats["data_ajuizamento"]["max"] = stats["data_ajuizamento"]["max"].isoformat()
    
    return stats

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Estatísticas dos processos"""
    
    por_tribunal = db.query(
        Processo.tribunal,
        func.count(Processo.id).label('count')
    ).group_by(Processo.tribunal).all()
    
    por_relevancia = db.query(
        Processo.relevancia,
        func.count(Processo.id).label('count')
    ).group_by(Processo.relevancia).all()
    
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

@router.get("/novos-hoje")
def get_novos_hoje(db: Session = Depends(get_db)):
    """Processos adicionados hoje"""
    from datetime import datetime
    hoje = datetime.now().date()
    
    count = db.query(func.count(Processo.id)).filter(
        func.date(Processo.created_at) == hoje
    ).scalar()
    
    return {"novos_hoje": count or 0, "data": hoje.isoformat()}

@router.get("/comarcas")
async def listar_comarcas():
    """Retorna lista de todas as comarcas TJSP e TJBA"""
    from src.utils.comarcas import COMARCAS_TJSP, COMARCAS_TJBA
    
    # Ordenar alfabeticamente
    tjsp_sorted = sorted(set(COMARCAS_TJSP.values()))
    tjba_sorted = sorted(set(COMARCAS_TJBA.values()))
    
    return {
        "TJSP": tjsp_sorted,
        "TJBA": tjba_sorted,
        "total": len(tjsp_sorted) + len(tjba_sorted)
    }

@router.get("/{process_id}")
def get_process(process_id: int, db: Session = Depends(get_db)):
    """Buscar processo por ID"""
    processo = db.query(Processo).filter(Processo.id == process_id).first()
    if not processo:
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    
    return {
        "id": processo.id,
        "numero_cnj": processo.numero_processo,
        "tribunal": processo.tribunal,
        "tipo_processo": processo.tipo_processo,
        "classe": processo.classe,
        "comarca": processo.comarca,
        "vara": processo.vara if hasattr(processo, 'vara') else None,
        "relevance": processo.relevancia,
        "score_relevancia": processo.score_relevancia,
        "data_ajuizamento": processo.data_ajuizamento.isoformat() if processo.data_ajuizamento else None,
        "valor_causa": processo.valor_causa,
        "created_at": processo.created_at.isoformat() if processo.created_at else None,
        "updated_at": processo.updated_at.isoformat() if processo.updated_at else None,
        "movimentacoes": processo.movimentacoes,
    }

@router.get("/{process_id}/link")
def get_link_tribunal(process_id: int, db: Session = Depends(get_db)):
    """Retorna link para consulta no tribunal"""
    processo = db.query(Processo).filter(Processo.id == process_id).first()
    if not processo:
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    
    return {
        "link": gerar_link_tribunal(processo.numero_processo, processo.tribunal),
        "tribunal": processo.tribunal,
        "numero": processo.numero_processo
    }

# ========================================
# ENDPOINT DE STATUS
# ========================================

from pydantic import BaseModel
from typing import Literal

class StatusUpdate(BaseModel):
    status: Literal["pendente", "interesse", "descartado"]

@router.patch("/{process_id}/status")
def update_process_status(
    process_id: int,
    status_update: StatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza o status de marcação de um processo.
    
    Status possíveis:
    - pendente: Não analisado (padrão)
    - interesse: Processo interessante
    - descartado: Processo descartado
    """
    processo = db.query(Processo).filter(Processo.id == process_id).first()
    
    if not processo:
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    
    # Atualizar status
    processo.status = status_update.status
    
    try:
        db.commit()
        db.refresh(processo)
        
        return {
            "success": True,
            "id": processo.id,
            "numero_cnj": processo.numero_processo,
            "status": processo.status,
            "message": f"Status atualizado para '{processo.status}'"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

