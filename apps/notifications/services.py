"""
Servicio de notificaciones con Redis
"""
import json
import redis
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from .models import (
    Notificacion, TipoNotificacion, PrioridadNotificacion,
    CanalNotificacion, PlantillaNotificacion
)

User = get_user_model()


class NotificationService:
    """
    Servicio para gestión de notificaciones en tiempo real usando Redis
    """
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        )
        self.channel_prefix = 'notifications:'
        self.user_channel_prefix = 'user_notifications:'
    
    def enviar_notificacion(self, usuario_id, tipo, titulo=None, mensaje=None, 
                          datos_adicionales=None, prioridad=None, expires_hours=24):
        """
        Enviar notificación a un usuario específico
        
        Args:
            usuario_id: ID del usuario destinatario
            tipo: Tipo de notificación (TipoNotificacion)
            titulo: Título personalizado (opcional, usa plantilla si no se proporciona)
            mensaje: Mensaje personalizado (opcional, usa plantilla si no se proporciona)
            datos_adicionales: Datos adicionales en formato dict
            prioridad: Prioridad de la notificación
            expires_hours: Horas hasta que expire la notificación
        
        Returns:
            Notificacion: La notificación creada
        """
        try:
            usuario = User.objects.get(id=usuario_id)
        except User.DoesNotExist:
            raise ValueError(f"Usuario con ID {usuario_id} no encontrado")
        
        # Verificar si el usuario puede recibir notificaciones
        canal = self._obtener_canal_usuario(usuario)
        if not canal.puede_recibir_notificacion(tipo):
            return None
        
        # Usar plantilla si no se proporciona título/mensaje
        if not titulo or not mensaje:
            plantilla_titulo, plantilla_mensaje = self._obtener_contenido_plantilla(
                tipo, datos_adicionales or {}
            )
            titulo = titulo or plantilla_titulo
            mensaje = mensaje or plantilla_mensaje
        
        # Determinar prioridad
        if not prioridad:
            prioridad = self._obtener_prioridad_default(tipo)
        
        # Calcular fecha de expiración
        expires_at = timezone.now() + timedelta(hours=expires_hours)
        
        # Crear notificación en base de datos
        notificacion = Notificacion.objects.create(
            usuario=usuario,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            prioridad=prioridad,
            datos_adicionales=datos_adicionales or {},
            expires_at=expires_at
        )
        
        # Enviar notificación en tiempo real via Redis
        self._enviar_tiempo_real(usuario, notificacion)
        
        # Incrementar contador de notificaciones no leídas
        self._incrementar_contador_no_leidas(usuario_id)
        
        return notificacion
    
    def enviar_notificacion_multiple(self, usuarios_ids, tipo, titulo=None, 
                                   mensaje=None, datos_adicionales=None, 
                                   prioridad=None, expires_hours=24):
        """
        Enviar notificación a múltiples usuarios
        
        Args:
            usuarios_ids: Lista de IDs de usuarios
            tipo: Tipo de notificación
            titulo: Título de la notificación
            mensaje: Mensaje de la notificación
            datos_adicionales: Datos adicionales
            prioridad: Prioridad de la notificación
            expires_hours: Horas hasta expiración
        
        Returns:
            list: Lista de notificaciones creadas
        """
        notificaciones = []
        
        for usuario_id in usuarios_ids:
            try:
                notificacion = self.enviar_notificacion(
                    usuario_id, tipo, titulo, mensaje, 
                    datos_adicionales, prioridad, expires_hours
                )
                if notificacion:
                    notificaciones.append(notificacion)
            except Exception as e:
                # Log error pero continúa con otros usuarios
                print(f"Error enviando notificación a usuario {usuario_id}: {e}")
        
        return notificaciones
    
    def enviar_a_hidrologica(self, hidrologica_id, tipo, titulo=None, 
                           mensaje=None, datos_adicionales=None, 
                           prioridad=None, excluir_usuarios=None):
        """
        Enviar notificación a todos los usuarios de una hidrológica
        
        Args:
            hidrologica_id: ID de la hidrológica
            tipo: Tipo de notificación
            titulo: Título de la notificación
            mensaje: Mensaje de la notificación
            datos_adicionales: Datos adicionales
            prioridad: Prioridad de la notificación
            excluir_usuarios: Lista de IDs de usuarios a excluir
        
        Returns:
            list: Lista de notificaciones creadas
        """
        usuarios = User.objects.filter(
            hidrologica_id=hidrologica_id,
            is_active=True
        )
        
        if excluir_usuarios:
            usuarios = usuarios.exclude(id__in=excluir_usuarios)
        
        usuarios_ids = list(usuarios.values_list('id', flat=True))
        
        return self.enviar_notificacion_multiple(
            usuarios_ids, tipo, titulo, mensaje, 
            datos_adicionales, prioridad
        )
    
    def enviar_a_ente_rector(self, tipo, titulo=None, mensaje=None, 
                           datos_adicionales=None, prioridad=None):
        """
        Enviar notificación a todos los usuarios del Ente Rector
        
        Args:
            tipo: Tipo de notificación
            titulo: Título de la notificación
            mensaje: Mensaje de la notificación
            datos_adicionales: Datos adicionales
            prioridad: Prioridad de la notificación
        
        Returns:
            list: Lista de notificaciones creadas
        """
        usuarios = User.objects.filter(
            rol=User.RolChoices.ADMIN_RECTOR,
            is_active=True
        )
        
        usuarios_ids = list(usuarios.values_list('id', flat=True))
        
        return self.enviar_notificacion_multiple(
            usuarios_ids, tipo, titulo, mensaje, 
            datos_adicionales, prioridad
        )
    
    def marcar_como_leida(self, notificacion_id, usuario_id):
        """
        Marcar notificación como leída
        
        Args:
            notificacion_id: ID de la notificación
            usuario_id: ID del usuario (para verificar permisos)
        
        Returns:
            bool: True si se marcó exitosamente
        """
        try:
            notificacion = Notificacion.objects.get(
                id=notificacion_id,
                usuario_id=usuario_id
            )
            
            if not notificacion.leida:
                notificacion.marcar_como_leida()
                
                # Decrementar contador de no leídas
                self._decrementar_contador_no_leidas(usuario_id)
                
                return True
            
            return False
            
        except Notificacion.DoesNotExist:
            return False
    
    def marcar_todas_como_leidas(self, usuario_id):
        """
        Marcar todas las notificaciones de un usuario como leídas
        
        Args:
            usuario_id: ID del usuario
        
        Returns:
            int: Número de notificaciones marcadas
        """
        notificaciones_no_leidas = Notificacion.objects.filter(
            usuario_id=usuario_id,
            leida=False
        )
        
        count = notificaciones_no_leidas.count()
        
        # Marcar todas como leídas
        notificaciones_no_leidas.update(
            leida=True,
            fecha_lectura=timezone.now()
        )
        
        # Resetear contador
        self._resetear_contador_no_leidas(usuario_id)
        
        return count
    
    def obtener_notificaciones_usuario(self, usuario_id, solo_no_leidas=False, 
                                     limit=50, offset=0):
        """
        Obtener notificaciones de un usuario
        
        Args:
            usuario_id: ID del usuario
            solo_no_leidas: Si solo retornar no leídas
            limit: Límite de resultados
            offset: Offset para paginación
        
        Returns:
            QuerySet: Notificaciones del usuario
        """
        queryset = Notificacion.objects.filter(usuario_id=usuario_id)
        
        if solo_no_leidas:
            queryset = queryset.filter(leida=False)
        
        # Excluir notificaciones expiradas
        queryset = queryset.filter(
            models.Q(expires_at__isnull=True) |
            models.Q(expires_at__gt=timezone.now())
        )
        
        return queryset.order_by('-created_at')[offset:offset + limit]
    
    def obtener_contador_no_leidas(self, usuario_id):
        """
        Obtener contador de notificaciones no leídas
        
        Args:
            usuario_id: ID del usuario
        
        Returns:
            int: Número de notificaciones no leídas
        """
        cache_key = f"notifications_unread_count:{usuario_id}"
        count = cache.get(cache_key)
        
        if count is None:
            # Recalcular desde base de datos
            count = Notificacion.objects.filter(
                usuario_id=usuario_id,
                leida=False
            ).filter(
                models.Q(expires_at__isnull=True) |
                models.Q(expires_at__gt=timezone.now())
            ).count()
            
            # Cachear por 5 minutos
            cache.set(cache_key, count, 300)
        
        return count
    
    def limpiar_notificaciones_expiradas(self):
        """
        Limpiar notificaciones expiradas (tarea de mantenimiento)
        
        Returns:
            int: Número de notificaciones eliminadas
        """
        count = Notificacion.objects.filter(
            expires_at__lt=timezone.now()
        ).count()
        
        Notificacion.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()
        
        return count
    
    def _enviar_tiempo_real(self, usuario, notificacion):
        """
        Enviar notificación en tiempo real via Redis
        """
        channel = f"{self.user_channel_prefix}{usuario.id}"
        
        mensaje = {
            'id': str(notificacion.id),
            'tipo': notificacion.tipo,
            'titulo': notificacion.titulo,
            'mensaje': notificacion.mensaje,
            'prioridad': notificacion.prioridad,
            'datos_adicionales': notificacion.datos_adicionales,
            'created_at': notificacion.created_at.isoformat(),
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            self.redis_client.publish(channel, json.dumps(mensaje))
        except Exception as e:
            # Log error pero no fallar
            print(f"Error enviando notificación en tiempo real: {e}")
    
    def _obtener_canal_usuario(self, usuario):
        """
        Obtener o crear canal de notificaciones del usuario
        """
        canal, created = CanalNotificacion.objects.get_or_create(
            usuario=usuario,
            defaults={
                'tipos_habilitados': [choice[0] for choice in TipoNotificacion.choices]
            }
        )
        return canal
    
    def _obtener_contenido_plantilla(self, tipo, variables):
        """
        Obtener contenido de plantilla para un tipo de notificación
        """
        try:
            plantilla = PlantillaNotificacion.objects.get(tipo=tipo, activa=True)
            return plantilla.generar_contenido(**variables)
        except PlantillaNotificacion.DoesNotExist:
            # Plantillas por defecto
            return self._obtener_plantilla_default(tipo, variables)
    
    def _obtener_plantilla_default(self, tipo, variables):
        """
        Plantillas por defecto para tipos de notificación
        """
        plantillas = {
            TipoNotificacion.NUEVA_SOLICITUD: (
                "Nueva solicitud de transferencia",
                "Se ha recibido una nueva solicitud de transferencia que requiere aprobación."
            ),
            TipoNotificacion.TRANSFERENCIA_APROBADA: (
                "Transferencia aprobada",
                "Su solicitud de transferencia ha sido aprobada y está lista para procesar."
            ),
            TipoNotificacion.TRANSFERENCIA_RECHAZADA: (
                "Transferencia rechazada",
                "Su solicitud de transferencia ha sido rechazada."
            ),
            TipoNotificacion.TRANSFERENCIA_EN_TRANSITO: (
                "Transferencia en tránsito",
                "La transferencia ha iniciado su tránsito."
            ),
            TipoNotificacion.TRANSFERENCIA_COMPLETADA: (
                "Transferencia completada",
                "La transferencia ha sido completada exitosamente."
            ),
            TipoNotificacion.MOVIMIENTO_INTERNO: (
                "Movimiento interno realizado",
                "Se ha realizado un movimiento interno de inventario."
            ),
            TipoNotificacion.SISTEMA: (
                "Notificación del sistema",
                "Mensaje del sistema."
            )
        }
        
        return plantillas.get(tipo, ("Notificación", "Nueva notificación del sistema"))
    
    def _obtener_prioridad_default(self, tipo):
        """
        Obtener prioridad por defecto según el tipo
        """
        prioridades = {
            TipoNotificacion.NUEVA_SOLICITUD: PrioridadNotificacion.ALTA,
            TipoNotificacion.TRANSFERENCIA_APROBADA: PrioridadNotificacion.ALTA,
            TipoNotificacion.TRANSFERENCIA_RECHAZADA: PrioridadNotificacion.MEDIA,
            TipoNotificacion.TRANSFERENCIA_EN_TRANSITO: PrioridadNotificacion.MEDIA,
            TipoNotificacion.TRANSFERENCIA_COMPLETADA: PrioridadNotificacion.MEDIA,
            TipoNotificacion.MOVIMIENTO_INTERNO: PrioridadNotificacion.BAJA,
            TipoNotificacion.SISTEMA: PrioridadNotificacion.MEDIA
        }
        
        return prioridades.get(tipo, PrioridadNotificacion.MEDIA)
    
    def _incrementar_contador_no_leidas(self, usuario_id):
        """Incrementar contador de notificaciones no leídas"""
        cache_key = f"notifications_unread_count:{usuario_id}"
        try:
            cache.delete(cache_key)  # Forzar recálculo en próxima consulta
        except Exception:
            pass
    
    def _decrementar_contador_no_leidas(self, usuario_id):
        """Decrementar contador de notificaciones no leídas"""
        cache_key = f"notifications_unread_count:{usuario_id}"
        try:
            cache.delete(cache_key)  # Forzar recálculo en próxima consulta
        except Exception:
            pass
    
    def _resetear_contador_no_leidas(self, usuario_id):
        """Resetear contador de notificaciones no leídas"""
        cache_key = f"notifications_unread_count:{usuario_id}"
        cache.set(cache_key, 0, 300)


# Instancia global del servicio
notification_service = NotificationService()


# Funciones de conveniencia para usar en otros módulos

def notificar_nueva_solicitud_transferencia(transferencia):
    """Notificar nueva solicitud de transferencia al Ente Rector"""
    return notification_service.enviar_a_ente_rector(
        tipo=TipoNotificacion.NUEVA_SOLICITUD,
        datos_adicionales={
            'transferencia_id': str(transferencia.id),
            'numero_orden': transferencia.numero_orden,
            'hidrologica_origen': transferencia.hidrologica_origen.nombre,
            'hidrologica_destino': transferencia.hidrologica_destino.nombre
        }
    )


def notificar_transferencia_aprobada(transferencia):
    """Notificar aprobación de transferencia al solicitante"""
    return notification_service.enviar_notificacion(
        usuario_id=transferencia.solicitado_por.id,
        tipo=TipoNotificacion.TRANSFERENCIA_APROBADA,
        datos_adicionales={
            'transferencia_id': str(transferencia.id),
            'numero_orden': transferencia.numero_orden
        }
    )


def notificar_transferencia_rechazada(transferencia, motivo):
    """Notificar rechazo de transferencia al solicitante"""
    return notification_service.enviar_notificacion(
        usuario_id=transferencia.solicitado_por.id,
        tipo=TipoNotificacion.TRANSFERENCIA_RECHAZADA,
        datos_adicionales={
            'transferencia_id': str(transferencia.id),
            'numero_orden': transferencia.numero_orden,
            'motivo_rechazo': motivo
        }
    )


def notificar_transferencia_en_transito(transferencia):
    """Notificar que transferencia está en tránsito"""
    # Notificar a hidrológica destino
    return notification_service.enviar_a_hidrologica(
        hidrologica_id=transferencia.hidrologica_destino.id,
        tipo=TipoNotificacion.TRANSFERENCIA_EN_TRANSITO,
        datos_adicionales={
            'transferencia_id': str(transferencia.id),
            'numero_orden': transferencia.numero_orden,
            'hidrologica_origen': transferencia.hidrologica_origen.nombre
        }
    )


def notificar_transferencia_completada(transferencia):
    """Notificar que transferencia fue completada"""
    # Notificar a ambas hidrológicas y al Ente Rector
    notificaciones = []
    
    # Hidrológica origen
    notificaciones.extend(
        notification_service.enviar_a_hidrologica(
            hidrologica_id=transferencia.hidrologica_origen.id,
            tipo=TipoNotificacion.TRANSFERENCIA_COMPLETADA,
            datos_adicionales={
                'transferencia_id': str(transferencia.id),
                'numero_orden': transferencia.numero_orden,
                'hidrologica_destino': transferencia.hidrologica_destino.nombre
            }
        )
    )
    
    # Ente Rector
    notificaciones.extend(
        notification_service.enviar_a_ente_rector(
            tipo=TipoNotificacion.TRANSFERENCIA_COMPLETADA,
            datos_adicionales={
                'transferencia_id': str(transferencia.id),
                'numero_orden': transferencia.numero_orden,
                'hidrologica_origen': transferencia.hidrologica_origen.nombre,
                'hidrologica_destino': transferencia.hidrologica_destino.nombre
            }
        )
    )
    
    return notificaciones


def notificar_movimiento_interno(movimiento):
    """Notificar movimiento interno"""
    return notification_service.enviar_a_hidrologica(
        hidrologica_id=movimiento.hidrologica.id,
        tipo=TipoNotificacion.MOVIMIENTO_INTERNO,
        datos_adicionales={
            'movimiento_id': str(movimiento.id),
            'item_sku': movimiento.item.sku,
            'acueducto_origen': movimiento.acueducto_origen.nombre,
            'acueducto_destino': movimiento.acueducto_destino.nombre
        },
        excluir_usuarios=[movimiento.usuario.id]  # No notificar al que hizo el movimiento
    )