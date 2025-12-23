"""
Celery configuration for inventory_platform project.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_platform.settings')

app = Celery('inventory_platform')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configuración de tareas periódicas
app.conf.beat_schedule = {
    # Limpiar notificaciones expiradas diariamente a las 2:00 AM
    'limpiar-notificaciones-expiradas': {
        'task': 'apps.notifications.tasks.limpiar_notificaciones_expiradas',
        'schedule': crontab(hour=2, minute=0),
    },
    # Limpiar notificaciones antiguas semanalmente los domingos a las 3:00 AM
    'limpiar-notificaciones-antiguas': {
        'task': 'apps.notifications.tasks.limpiar_notificaciones_antiguas',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),
        'kwargs': {'dias_antiguedad': 90}
    },
    # Generar reporte mensual el primer día del mes a las 4:00 AM
    'generar-reporte-notificaciones': {
        'task': 'apps.notifications.tasks.generar_reporte_notificaciones',
        'schedule': crontab(hour=4, minute=0, day_of_month=1),
    },
    # Enviar resumen diario a las 8:00 AM
    'resumen-notificaciones-diario': {
        'task': 'apps.notifications.tasks.enviar_resumen_notificaciones_diario',
        'schedule': crontab(hour=8, minute=0),
    },
}

app.conf.timezone = 'UTC'