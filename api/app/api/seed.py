from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Process, Party
from datetime import datetime, timedelta
import random

router = APIRouter()

@router.post("/seed")
async def seed_database(db: Session = Depends(get_db)):
    """Popular banco com dados de teste"""
    
    # Limpar dados existentes
    db.query(Party).delete()
    db.query(Process).delete()
    db.commit()
    
    # Criar 50 processos de teste
    tribunais = ["TJSP", "TJRJ", "TJMG", "TJRS"]
    tipos = ["Cível", "Criminal", "Trabalhista", "Tributário"]
    
    for i in range(50):
        process = Process(
            number=f"0001234-56.2024.8.26.{1000+i:04d}",
            tribunal=random.choice(tribunais),
            type=random.choice(tipos),
            status="Em andamento" if i % 3 else "Concluído",
            filing_date=datetime.now() - timedelta(days=random.randint(1, 365)),
            last_update=datetime.now() - timedelta(days=random.randint(0, 30)),
            subject=f"Processo teste {i+1}",
            value=random.uniform(1000, 100000),
            judge=f"Juiz(a) Teste {random.randint(1, 10)}"
        )
        db.add(process)
        db.flush()
        
        # Adicionar partes
        for j in range(2):
            party = Party(
                name=f"Parte {j+1} do Processo {i+1}",
                type="Autor" if j == 0 else "Réu",
                process_id=process.id
            )
            db.add(party)
    
    db.commit()
    
    return {"message": "Banco populado com 50 processos de teste!"}
