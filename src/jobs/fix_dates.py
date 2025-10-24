import sys
sys.path.insert(0, '/app')
from datetime import datetime, timedelta
import random
from src.database import SessionLocal
from src.normalization.models import Process, Movement

def fix_dates():
    db = SessionLocal()
    print("Corrigindo datas...")
    processes = db.query(Process).all()
    for process in processes:
        if not process.data_distribuicao:
            dias = random.randint(30, 730)
            process.data_distribuicao = datetime.now() - timedelta(days=dias)
        movements = db.query(Movement).filter(Movement.process_id == process.id).all()
        if movements:
            data = process.data_distribuicao
            for m in movements:
                data = data + timedelta(days=random.randint(5, 45))
                if data > datetime.now():
                    data = datetime.now() - timedelta(days=random.randint(1, 30))
                m.data_movimento = data
    db.commit()
    print("Datas corrigidas!")
    db.close()

if __name__ == "__main__":
    fix_dates()
