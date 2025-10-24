from sqlalchemy import Column, Integer, String, Float, DateTime, ARRAY, ForeignKey, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Process(Base):
    __tablename__ = 'processes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_cnj = Column(String(25), unique=True, nullable=False, index=True)
    tribunal = Column(String(10), nullable=False, index=True)
    classe_tpu = Column(String(10), nullable=False, index=True)
    assunto_tpu = Column(ARRAY(String), nullable=True)
    orgao = Column(String(255))
    vara = Column(String(255))
    comarca = Column(String(255), index=True)
    valor_causa = Column(Float)
    relevance = Column(String(20), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    parties = relationship("Party", back_populates="process", cascade="all, delete-orphan")
    movements = relationship("Movement", back_populates="process", cascade="all, delete-orphan")

class Party(Base):
    __tablename__ = 'parties'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    process_id = Column(Integer, ForeignKey('processes.id', ondelete='CASCADE'), nullable=False, index=True)
    tipo = Column(String(50), nullable=False)
    nome = Column(String(255), nullable=False)
    documento_hash = Column(String(64))
    
    process = relationship("Process", back_populates="parties")

class Movement(Base):
    __tablename__ = 'movements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    process_id = Column(Integer, ForeignKey('processes.id', ondelete='CASCADE'), nullable=False, index=True)
    data = Column(DateTime, nullable=False, index=True)
    tipo_tpu = Column(String(10), nullable=False)
    descricao_raw = Column(String)
    descricao_norm = Column(String)
    relevance = Column(String(20), index=True)
    hash_idem = Column(String(64), unique=True, nullable=False)
    
    process = relationship("Process", back_populates="movements")
    
    __table_args__ = (
        UniqueConstraint('hash_idem', name='uix_movement_hash'),
        Index('idx_movement_process_data', 'process_id', 'data'),
    )
