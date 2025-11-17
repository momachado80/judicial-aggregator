from sqlalchemy import Column, Integer, String, Date, Float, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ProcessoDJE(Base):
    __tablename__ = "processos_dje"
    
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, unique=True, index=True, nullable=False)
    tipo = Column(String, index=True)
    classe = Column(String)
    comarca = Column(String, index=True)
    codigo_comarca = Column(String, index=True)
    partes = Column(JSON)
    advogados = Column(JSON)
    valor_causa = Column(String)
    data_dje = Column(String)
    caderno = Column(String)
    pagina_dje = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
