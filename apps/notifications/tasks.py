"""
Tareas de Celery para notificaciones
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .services import notification_service
from .models import Notificacion


@shared_task
def limpiar_notificaciones_expiradas():
    """
    Tarea para limpiar notificaciones expiradas
    Se ejecuta diariamente
    """
    try:
        count = notification_service.limpiar_notificaciones_expiradas()
        return f"Se eliminaron {count} notificaciones expiradas"
    except Exception as e:
        return f"Error limpiando notificaciones: {str(e)}"


@shared_task
def limpiar_notificaciones_antiguas(dias_antiguedad=90):
    """
    Tarea para limpiar notificaciones muy antiguas (leídas)
    Se ejecuta semanalmente
    
    Args:
        dias_antiguedad: Días de antigüedad para considerar una notificación como antigua
    """
    try:
        fecha_limite = timezone.now() - timedelta(days=dias_antiguedad)
        
        count = Notificacion.objects.filter(
            leida=True,
            fecha_lectura__lt=fecha_limite
        ).count()
        
        Notificacion.objects.filter(
            leida=True,
            fecha_lectura__lt=fecha_limite
        ).delete()
        
        return f"Se eliminaron {count} notificaciones antiguas (más de {dias_antiguedad} días)"
    except Exception as e:
        return f"Error limpiando notificaciones antiguas: {str(e)}"


@shared_task
def generar_reporte_notificaciones():
    """
    Tarea para generar reporte de estadísticas de notificaciones
    Se ejecuta mensualmente
    """
    try:
        from django.db.models import Count, Q
        from datetime import datetime
        
        # Estadísticas del último mes
        fecha_inicio = timezone.now() - timedelta(days=30)
        
        stats = {
            'periodo': '30 días',
            'fecha_generacion': timezone.now().isoformat(),
            'total_enviadas': Notificacion.objects.filter(
                created_at__gte=fecha_inicio
            ).count(),
            'total_leidas': Notificacion.objects.filter(
                created_at__gte=fecha_inicio,
                leida=True
            ).count(),
            'por_tipo': {},
            'por_prioridad': {}
        }
        
        # Por tipo
        tipos_stats = Notificacion.objects.filter(
            created_at__gte=fecha_inicio
        ).values('tipo').annotate(
            total=Count('id'),
            leidas=Count('id', filter=Q(leida=True))
        )
        
        for item in tipos_stats:
            stats['por_tipo'][item['tipo']] = {
                'total': item['total'],
                'leidas': item['leidas'],
                'porcentaje_lectura': (item['leidas'] / item['total'] * 100) if item['total'] > 0 else 0
            }
        
        # Por prioridad
        prioridades_stats = Notificacion.objects.filter(
            created_at__gte=fecha_inicio
        ).values('prioridad').annotate(
            total=Count('id'),
            leidas=Count('id', filter=Q(leida=True))
        )
        
        for item in prioridades_stats:
            stats['por_prioridad'][item['prioridad']] = {
                'total': item['total'],
                'leidas': item['leidas'],
                'porcentaje_lectura': (item['leidas'] / item['total'] * 100) if item['total'] > 0 else 0
            }
        
        # Calcular porcentaje general
        if stats['total_enviadas'] > 0:
            stats['porcentaje_lectura_general'] = (stats['total_leidas'] / stats['total_enviadas']) * 100
        else:
            stats['porcentaje_lectura_general'] = 0
        
        # Aquí se podría enviar el reporte por email o guardarlo en un archivo
        # Por ahora solo retornamos las estadísticas
        
        return f"Reporte generado: {stats['total_enviadas']} enviadas, {stats['total_leidas']} leídas ({stats['porcentaje_lectura_general']:.1f}%)"
        
    except Exception as e:
        return f"Error generando reporte: {str(e)}"


@shared_task
def enviar_resumen_notificaciones_diario():
    """
    Tarea para enviar resumen diario de notificaciones a administradores
    Se ejecuta diariamente
    """
    try:
        from django.contrib.auth import get_user_model
        from .models import TipoNotificacion
        
        User = get_user_model()
        
        # Obtener estadísticas del día
        fecha_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_enviadas = Notificacion.objects.filter(
            created_at__gte=fecha_inicio
        ).count()
        
        if total_enviadas == 0:
            return "No hay notificaciones para reportar hoy"
        
        # Enviar resumen a administradores del Ente Rector
        admins = User.objects.filter(
            rol=User.RolChoices.ADMIN_RECTOR,
            is_active=True
        )
        
        for admin in admins:
            notification_service.enviar_notificacion(
                usuario_id=admin.id,
                tipo=TipoNotificacion.SISTEMA,
                titulo="Resumen diario de notificaciones",
                mensaje=f"Se enviaron {total_enviadas} notificaciones en el día de hoy.",
                datos_adicionales={
                    'tipo_reporte': 'resumen_diario',
                    'fecha': fecha_inicio.date().isoformat(),
                    'total_enviadas': total_enviadas
                },
                expires_hours=48
            )
        
        return f"Resumen diario enviado a {admins.count()} administradores"
        
    except Exception as e:
        return f"Error enviando resumen diario: {str(e)}"


@shared_task
def procesar_notificaciones_batch(notificaciones_data):
    """
    Tarea para procesar notificaciones en lote
    Útil para envíos masivos sin bloquear la aplicación
    
    Args:
        notificaciones_data: Lista de diccionarios con datos de notificaciones
    """
    try:
        enviadas = 0
        errores = 0
        
        for notif_data in notificaciones_data:
            try:
                notification_service.enviar_notificacion(**notif_data)
                enviadas += 1
            except Exception as e:
                errores += 1
                # Log del error específico
                print(f"Error enviando notificación: {e}")
        
        return f"Procesamiento completado: {enviadas} enviadas, {errores} errores"
        
    except Exception as e:
        return f"Error en procesamiento batch: {str(e)}"