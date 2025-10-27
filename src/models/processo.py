from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.sql import func
from src.database import Base

class Processo(Base):
    __tablename__ = "processos"

    id = Column(Integer, primary_key=True, index=True)
    numero_processo = Column(String(50), unique=True, index=True, nullable=False)
    tribunal = Column(String(10), index=True, nullable=False)  # TJSP, TJBA
    tipo_processo = Column(String(50), index=True, nullable=False)  # Inventário, Divórcio
    classe = Column(String(100))
    assunto = Column(String(200))
    data_ajuizamento = Column(DateTime)
    valor_causa = Column(Float)
    comarca = Column(String(100))
    vara = Column(String(100))
    juiz = Column(String(200))
    partes = Column(Text)  # JSON string
    movimentacoes = Column(Text)  # JSON string
    relevancia = Column(String(20), index=True)  # Alta, Média, Baixa
    score_relevancia = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Processo {self.numero_processo} - {self.tribunal}>"
