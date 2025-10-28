import sys
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.normalization.models import Base, Process, Party, Movement

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://jud_user:jud_pass@db:5432/jud_agg')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def gerar_cnj_correto(tribunal):
    """Gera número CNJ no formato: NNNNNNN-DD.AAAA.J.TT.OOOO"""
    seq = random.randint(100000, 999999)
    dv = random.randint(10, 99)
    ano = random.randint(2023, 2025)
    codigo = '26' if tribunal == 'TJSP' else '05'
    vara = random.randint(100, 9999)
    return f"{seq:07d}-{dv}.{ano}.8.{codigo}.{vara:04d}"

def seed_processes():
    db = SessionLocal()
    try:
        print("🧹 Limpando banco...")
        db.query(Movement).delete()
        db.query(Party).delete()
        db.query(Process).delete()
        db.commit()
        
        print("🌱 Criando 100 processos com números CNJ CORRETOS...")
        
        for i in range(100):
            tribunal = random.choice(['TJSP', 'TJBA'])
            numero = gerar_cnj_correto(tribunal)
            
            process = Process(
                numero_cnj=numero,
                tribunal=tribunal,
                classe_tpu='8015' if i % 2 == 0 else '8016',
                assunto_tpu=['1175'],
                orgao=f"{random.randint(1,10)}ª Vara",
                vara="Vara de Família",
                comarca=random.choice(['São Paulo', 'Salvador']),
                valor_causa=round(random.uniform(10000, 500000), 2),
                relevance=random.choice(['Alta', 'Média', 'Baixa'])
            )
            db.add(process)
            db.flush()
            
            # Partes
            for j in range(random.randint(2, 4)):
                party = Party(
                    process_id=process.id,
                    tipo=random.choice(['Autor', 'Réu']),
                    nome=random.choice(['João Silva', 'Maria Santos']),
                    documento_hash=f"hash_{random.randint(10000,99999)}"
                )
                db.add(party)
            
            # Movimentos
            base_date = datetime.now() - timedelta(days=random.randint(30, 200))
            for k in range(random.randint(3, 8)):
                movement = Movement(
                    process_id=process.id,
                    data=base_date + timedelta(days=k*10),
                    tipo_tpu=str(random.randint(1, 999)),
                    descricao_raw="Movimento processual",
                    descricao_norm="Movimento",
                    relevance=random.choice(['Alta', 'Média', 'Baixa']),
                    hash_idem=f"hash_{process.id}_{k}"
                )
                db.add(movement)
            
            if (i + 1) % 20 == 0:
                print(f"✅ {i + 1} processos criados...")
        
        db.commit()
        
        # VERIFICAÇÃO DOS CÓDIGOS
        print("\n📊 VERIFICANDO CÓDIGOS DOS TRIBUNAIS:")
        result = db.execute("""
            SELECT 
                tribunal,
                SUBSTRING(numero_cnj FROM 15 FOR 4) as codigo,
                COUNT(*) as qtd
            FROM processes 
            GROUP BY tribunal, codigo
            ORDER BY tribunal, qtd DESC
        """)
        
        for row in result:
            emoji = "✅" if row[1] in ['8.26', '8.05'] else "❌"
            print(f"{emoji} {row[0]}: código '{row[1]}' = {row[2]} processos")
        
        total = db.query(Process).count()
        print(f"\n🎉 CONCLUÍDO! {total} processos no banco.")
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    seed_processes()
