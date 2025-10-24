import sys
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.normalization.models import Base, Process, Party, Movement

# Configuração do banco
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://jud_user:jud_pass@db:5432/jud_agg')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def generate_cnj():
    """Gera um número CNJ fictício"""
    ano = random.randint(2023, 2025)
    seq = random.randint(1, 999999)
    origem = random.choice(['8.26', '8.05'])  # TJSP ou TJBA
    comarca = random.randint(1, 9999)
    return f"{seq:07d}-{random.randint(10,99)}.{ano}.{origem}.{comarca:04d}"

def seed_processes():
    """Popula o banco com processos de demonstração"""
    db = SessionLocal()
    
    try:
        print("🌱 Iniciando seed de dados...")
        
        tribunais = ['TJSP', 'TJBA']
        classes = [
            {'codigo': '8015', 'nome': 'Divórcio', 'assunto': '1175'},
            {'codigo': '8016', 'nome': 'Inventário', 'assunto': '1176'}
        ]
        comarcas = ['São Paulo', 'Salvador', 'Campinas', 'Feira de Santana', 'Santos', 'Camaçari']
        relevances = ['Alta', 'Média', 'Baixa']
        
        processos_criados = 0
        
        for i in range(50):  # Criar 50 processos
            tribunal = random.choice(tribunais)
            classe = random.choice(classes)
            
            process = Process(
                numero_cnj=generate_cnj(),
                tribunal=tribunal,
                classe_tpu=classe['codigo'],
                assunto_tpu=[classe['assunto']],
                orgao=f"{random.randint(1,10)}ª Vara",
                vara=f"Vara de Família e Sucessões",
                comarca=random.choice(comarcas),
                valor_causa=round(random.uniform(10000, 500000), 2) if random.random() > 0.3 else None,
                relevance=random.choice(relevances)
            )
            
            db.add(process)
            db.flush()
            
            # Adicionar partes
            num_partes = random.randint(2, 4)
            tipos_parte = ['Autor', 'Réu', 'Interessado', 'Inventariante', 'Herdeiro']
            nomes = [
                'João da Silva', 'Maria Santos', 'Pedro Oliveira', 'Ana Costa',
                'Carlos Souza', 'Juliana Lima', 'Roberto Alves', 'Fernanda Rocha'
            ]
            
            for j in range(num_partes):
                party = Party(
                    process_id=process.id,
                    tipo=random.choice(tipos_parte),
                    nome=random.choice(nomes),
                    documento_hash=f"hash_{random.randint(10000,99999)}"
                )
                db.add(party)
            
            # Adicionar movimentos
            num_movimentos = random.randint(3, 10)
            tipos_movimento = [
                'Distribuição', 'Despacho', 'Intimação', 'Sentença',
                'Conclusão', 'Juntada de Petição', 'Decisão', 'Penhora',
                'Homologação', 'Partilha'
            ]
            
            base_date = datetime.now() - timedelta(days=random.randint(30, 365))
            
            for k in range(num_movimentos):
                movement_date = base_date + timedelta(days=k * random.randint(5, 30))
                tipo = random.choice(tipos_movimento)
                
                movement = Movement(
                    process_id=process.id,
                    data=movement_date,
                    tipo_tpu=str(random.randint(1, 999)),
                    descricao_raw=f"{tipo} - Movimento processual registrado",
                    descricao_norm=f"{tipo}",
                    relevance=random.choice(relevances),
                    hash_idem=f"hash_{process.id}_{k}_{random.randint(1000,9999)}"
                )
                db.add(movement)
            
            processos_criados += 1
            
            if processos_criados % 10 == 0:
                print(f"✓ {processos_criados} processos criados...")
        
        db.commit()
        print(f"\n✅ Seed concluído! {processos_criados} processos criados com sucesso!")
        print(f"📊 Acesse http://localhost:3000 para visualizar")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao criar seed: {e}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    # Criar tabelas se não existirem
    Base.metadata.create_all(engine)
    seed_processes()
