import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSON as PGJSON
from datetime import datetime

Base = declarative_base()

class ProcessoDJE(Base):
    __tablename__ = "processos_dje"
    
    id = Column(Integer, primary_key=True)
    numero = Column(String, unique=True, nullable=False)
    tipo = Column(String)
    classe = Column(String)
    comarca = Column(String)
    codigo_comarca = Column(String)
    partes = Column(PGJSON)
    advogados = Column(PGJSON)
    valor_causa = Column(String)
    data_dje = Column(String)
    caderno = Column(String)
    pagina_dje = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

from dje_parser_otimizado import extrair_processos_dje_otimizado

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL não definida")
    sys.exit(1)

print(f"🔗 Conectando em: {DATABASE_URL[:30]}...")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def salvar_processos(pdf_path: str, caderno: str, data_dje: str):
    print(f"📄 Processando: {pdf_path}")
    
    processos = extrair_processos_dje_otimizado(pdf_path, max_paginas=None)
    
    db = SessionLocal()
    salvos = 0
    duplicados = 0
    erros = 0
    
    for i, p in enumerate(processos, 1):
        try:
            processo = ProcessoDJE(
                numero=p['numero'],
                tipo=p['tipo'],
                comarca=p.get('comarca', 'Desconhecida'),
                codigo_comarca=p['codigo_comarca'],
                partes=[],
                advogados=[],
                data_dje=data_dje,
                caderno=caderno
            )
            db.add(processo)
            db.commit()
            salvos += 1
            if salvos % 100 == 0:
                print(f"   ✅ {salvos} salvos...")
        except Exception as e:
            db.rollback()
            if 'duplicate' in str(e).lower():
                duplicados += 1
            else:
                erros += 1
                if erros <= 3:  # Mostrar primeiros 3 erros
                    print(f"   ❌ Erro ao salvar processo {i}: {str(e)[:100]}")
    
    db.close()
    
    print(f"\n📊 RESULTADO:")
    print(f"   ✅ Salvos: {salvos}")
    print(f"   ⚠️  Duplicados: {duplicados}")
    print(f"   ❌ Erros: {erros}")

if __name__ == "__main__":
    salvar_processos(
        pdf_path="data/dje_pdfs/dje_14-11-2025_cad12.pdf",
        caderno="12",
        data_dje="14/11/2025"
    )
