"""Job para sincronizar processos diariamente"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Processo

async def sync_daily_processes():
    """Busca novos processos das últimas 24 horas"""
    print(f"🔄 Iniciando sincronização diária - {datetime.now()}")
    
    db = next(get_db())
    
    # Aqui você pode adicionar a lógica para:
    # 1. Buscar processos da API DataJud das últimas 24h
    # 2. Salvar no banco
    # 3. Notificar sobre novos processos
    
    yesterday = datetime.now() - timedelta(days=1)
    
    # Exemplo: contar processos novos
    novos = db.query(Processo).filter(
        Processo.created_at >= yesterday
    ).count()
    
    print(f"✅ Sincronização concluída! {novos} processos novos nas últimas 24h")
    
    return novos

if __name__ == "__main__":
    asyncio.run(sync_daily_processes())
