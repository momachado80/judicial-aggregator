from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSON as PGJSON
from datetime import datetime
import os

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

if __name__ == "__main__":
    # Conectar ao banco
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/judicial_aggregator")
    
    # Railway precisa de postgresql:// (sem +psycopg2)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(DATABASE_URL)
    
    print("🗄️  Criando tabela processos_dje...")
    Base.metadata.create_all(engine)
    print("✅ Tabela criada com sucesso!")
