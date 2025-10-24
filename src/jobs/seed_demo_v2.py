import sys
sys.path.insert(0, '/app')

from datetime import datetime, timedelta
import random
from src.database import SessionLocal
from src.normalization.models import Process, Party, Movement

def clear_database():
    db = SessionLocal()
    try:
        db.query(Movement).delete()
        db.query(Party).delete()
        db.query(Process).delete()
        db.commit()
        print("✓ Banco limpo")
    finally:
        db.close()

def seed_processes():
    db = SessionLocal()
    
    movimentos_divorcio = [
        "Distribuição do processo",
        "Citação realizada",
        "Contestação apresentada",
        "Audiência designada",
        "Acordo homologado",
        "Sentença proferida",
        "Trânsito em julgado"
    ]
    
    movimentos_inventario = [
        "Distribuição",
        "Nomeação de inventariante",
        "Primeiras declarações",
        "Citação dos herdeiros",
        "Avaliação de bens",
        "Pagamento de tributos",
        "Partilha homologada"
    ]
    
    comarcas_tjsp = ["São Paulo", "Campinas", "Santos", "Ribeirão Preto"]
    comarcas_tjba = ["Salvador", "Feira de Santana", "Camaçari"]
    
    nomes = ["Maria Silva", "João Santos", "Ana Costa", "Pedro Oliveira", "Carla Lima"]
    
    print("Criando 50 processos...")
    
    for i in range(1, 51):
        tribunal = "TJSP" if i % 2 == 0 else "TJBA"
        classe = "8015" if i % 2 == 0 else "8016"
        comarca = random.choice(comarcas_tjsp if tribunal == "TJSP" else comarcas_tjba)
        
        ano = random.choice([2023, 2024, 2025])
        segmento = "8.26" if tribunal == "TJSP" else "8.05"
        numero_cnj = f"{random.randint(100000, 999999):07d}-{random.randint(10, 99)}.{ano}.{segmento}.{random.randint(1000, 9999)}"
        
        if classe == "8015":
            valor_causa = random.choice([None, random.uniform(5000, 150000)])
        else:
            valor_causa = random.uniform(50000, 5000000)
        
        keywords_count = 0
        if valor_causa and valor_causa > 500000:
            keywords_count += 2
        if random.random() > 0.7:
            keywords_count += 1
            
        if keywords_count >= 2:
            relevance = "Alta"
        elif keywords_count == 1:
            relevance = "Média"
        else:
            relevance = "Baixa"
        
        dias_atras = random.randint(30, 730)
        data_distribuicao = datetime.now() - timedelta(days=dias_atras)
        
        process = Process(
            numero_cnj=numero_cnj,
            tribunal=tribunal,
            classe_tpu=classe,
            assunto_tpu=["1175" if classe == "8015" else "1176"],
            comarca=comarca,
            vara="Vara de Família e Sucessões",
            valor_causa=valor_causa,
            relevance=relevance,
            data_distribuicao=data_distribuicao
        )
        
        db.add(process)
        db.flush()
        
        for j in range(random.randint(2, 4)):
            tipo = random.choice(["Autor", "Réu", "Inventariante", "Herdeiro"])
            party = Party(
                process_id=process.id,
                tipo=tipo,
                nome=random.choice(nomes)
            )
            db.add(party)
        
        movimentos = movimentos_inventario if classe == "8016" else movimentos_divorcio
        data_atual = data_distribuicao
        
        for j in range(random.randint(3, 7)):
            dias_incremento = random.randint(5, 45)
            data_atual = data_atual + timedelta(days=dias_incremento)
            
            if data_atual > datetime.now():
                data_atual = datetime.now() - timedelta(days=random.randint(1, 30))
            
            movement = Movement(
                process_id=process.id,
                data_movimento=data_atual,
                descricao=movimentos[min(j, len(movimentos)-1)]
            )
            db.add(movement)
        
        if i % 10 == 0:
            print(f"  ✓ {i} processos")
    
    try:
        db.commit()
        print(f"\n✅ 50 processos criados!")
    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_database()
    seed_processes()
