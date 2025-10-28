"""
Job diário para coletar novos processos da API DataJud
Roda automaticamente todo dia às 2h da manhã
"""
from celery import Celery
from src.scrapers.datajud_collector import DataJudCollector
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurar Celery
celery_app = Celery('judicial_aggregator')
celery_app.config_from_object('src.celery_config')

@celery_app.task(name='daily_collector')
def coletar_processos_diarios():
    """
    Coleta novos processos diariamente
    - Limita a 1000 processos por tipo para não sobrecarregar
    - Processos duplicados são ignorados automaticamente
    """
    logger.info("🚀 Iniciando coleta diária de processos...")
    
    try:
        collector = DataJudCollector()
        novos, duplicados = collector.coletar_tudo(max_por_tipo=1000)
        
        logger.info(f"✅ Coleta concluída!")
        logger.info(f"   📊 Novos: {novos:,}")
        logger.info(f"   🔄 Duplicados: {duplicados:,}")
        
        return {
            "status": "success",
            "novos": novos,
            "duplicados": duplicados
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na coleta diária: {e}")
        raise

@celery_app.task(name='test_collector')
def testar_coleta():
    """Teste rápido com apenas 10 processos"""
    logger.info("🧪 Teste de coleta...")
    
    collector = DataJudCollector()
    novos, dup = collector.coletar_e_salvar('TJSP', 'Inventário', max_processos=10)
    
    logger.info(f"✅ Teste OK: {novos} novos, {dup} duplicados")
    return {"novos": novos, "duplicados": dup}

# Configurar schedule (todo dia às 2h da manhã)
celery_app.conf.beat_schedule = {
    'coleta-diaria-2am': {
        'task': 'daily_collector',
        'schedule': 7200.0,  # A cada 2 horas (para teste)
        # Para produção, use crontab:
        # 'schedule': crontab(hour=2, minute=0),  # Todo dia às 2h
    },
}

celery_app.conf.timezone = 'America/Sao_Paulo'

if __name__ == '__main__':
    # Executar manualmente
    coletar_processos_diarios()
