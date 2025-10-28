"""
Configuração do Celery para jobs agendados
"""
import os
from celery.schedules import crontab

# Redis como broker
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

# Configurações
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'America/Sao_Paulo'
enable_utc = False

# Schedule de tasks
beat_schedule = {
    'coleta-diaria-processos': {
        'task': 'daily_collector',
        'schedule': crontab(hour=2, minute=0),  # Todo dia às 2h da manhã
        'options': {'expires': 3600}
    },
}
