from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSON as PGJSON
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import os

router = APIRouter(prefix="/dje", tags=["DJE"])

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/judicial_aggregator")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
Base = declarative_base()

class ProcessoDJE(Base):
    __tablename__ = "processos_dje"
    
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, unique=True, index=True, nullable=False)
    tipo = Column(String, index=True)
    classe = Column(String)
    comarca = Column(String, index=True)
    codigo_comarca = Column(String, index=True)
    partes = Column(PGJSON)
    advogados = Column(PGJSON)
    valor_causa = Column(String)
    data_dje = Column(String)
    caderno = Column(String)
    pagina_dje = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic models
class ProcessoDJECreate(BaseModel):
    numero: str
    tipo: Optional[str] = None
    classe: Optional[str] = None
    comarca: Optional[str] = None
    codigo_comarca: Optional[str] = None
    partes: Optional[List] = []
    advogados: Optional[List] = []
    valor_causa: Optional[str] = None
    data_dje: Optional[str] = None
    caderno: Optional[str] = None
    pagina_dje: Optional[int] = None

class ProcessoDJEResponse(ProcessoDJECreate):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Dependency
def get_db():
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[ProcessoDJEResponse])
def listar_processos(
    tipo: Optional[str] = None,
    comarca: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista processos do DJE com filtros"""
    query = db.query(ProcessoDJE)
    
    if tipo:
        query = query.filter(ProcessoDJE.tipo == tipo)
    if comarca:
        query = query.filter(ProcessoDJE.comarca.ilike(f"%{comarca}%"))
    
    return query.offset(skip).limit(limit).all()

@router.get("/stats/resumo")
def estatisticas(db: Session = Depends(get_db)):
    """Estatísticas gerais"""
    from sqlalchemy import func
    
    total = db.query(func.count(ProcessoDJE.id)).scalar()
    por_tipo = db.query(
        ProcessoDJE.tipo,
        func.count(ProcessoDJE.id)
    ).group_by(ProcessoDJE.tipo).all()
    
    return {
        "total": total,
        "por_tipo": {tipo: count for tipo, count in por_tipo}
    }
