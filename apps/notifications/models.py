"""
Modelos para notificaciones
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import Hidrologica

User = get_user_model()


class TipoNotificacion(models.TextChoices):
    """Tipos de notificaciones del sistema"""
    NUEVA_SOLICITUD = 'nueva_solicitud', 'Nueva Solicitud de Transferencia'
    TRANSFERENCIA_APROBADA = 'transferencia_aprobada', 'Transferencia Aprobada'
    TRANSFERENCIA_RECHAZADA = 'transferencia_rechazada', 'Transferencia Rechazada'
    TRANSFERENCIA_EN_TRANSITO = 'transferencia_en_transito', 'Transferencia en Tránsito'
    TRANSFERENCIA_COMPLETADA = 'transferencia_completada', 'Transferencia Completada'
    MOVIMIENTO_INTERNO = 'movimiento_interno', 'Movimiento Interno Realizado'
    ITEM_ESTADO_CAMBIADO = 'item_estado_cambiado', 'Estado de Ítem Cambiado'
    SISTEMA = 'sistema', 'Notificación del Sistema'


class PrioridadNotificacion(models.TextChoices):
    """Prioridades de notificaciones"""
    BAJA = 'baja', 'Baja'
    MEDIA = 'media', 'Media'
    ALTA = 'alta', 'Alta'
    URGENTE = 'urgente', 'Urgente'


class Notificacion(models.Model):
    """
    Modelo para notificaciones del sistema
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Destinatario
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name="Usuario"
    )
    
    # Contenido de la notificación
    tipo = models.CharField(
        max_length=30,
        choices=TipoNotificacion.choices,
        verbose_name="Tipo"
    )
    titulo = models.CharField(max_length=200, verbose_name="Título")
    mensaje = models.TextField(verbose_name="Mensaje")
    prioridad = models.CharField(
        max_length=10,
        choices=PrioridadNotificacion.choices,
        default=PrioridadNotificacion.MEDIA,
        verbose_name="Prioridad"
    )
    
    # Datos adicionales (JSON)
    datos_adicionales = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Datos Adicionales",
        help_text="Información adicional como IDs de transferencias, ítems, etc."
    )
    
    # Estado de la notificación
    leida = models.BooleanField(default=False, verbose_name="Leída")
    fecha_lectura = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Lectura")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Expiración")
    
    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['usuario', 'leida']),
            models.Index(fields=['usuario', 'tipo']),
            models.Index(fields=['created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"

    def marcar_como_leida(self):
        """Marcar notificación como leída"""
        if not self.leida:
            from django.utils import timezone
            self.leida = True
            self.fecha_lectura = timezone.now()
            self.save(update_fields=['leida', 'fecha_lectura'])

    @property
    def es_urgente(self):
        """Verificar si la notificación es urgente"""
        return self.prioridad == PrioridadNotificacion.URGENTE

    @property
    def esta_expirada(self):
        """Verificar si la notificación está expirada"""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False


def default_dias_habilitados():
    """Días habilitados por defecto (Lunes a Viernes)"""
    return [0, 1, 2, 3, 4]


class CanalNotificacion(models.Model):
    """
    Configuración de canales de notificación por usuario
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='canal_notificaciones',
        verbose_name="Usuario"
    )
    
    # Configuración de canales
    email_habilitado = models.BooleanField(default=True, verbose_name="Email Habilitado")
    push_habilitado = models.BooleanField(default=True, verbose_name="Push Habilitado")
    
    # Configuración por tipo de notificación
    tipos_habilitados = models.JSONField(
        default=list,
        verbose_name="Tipos Habilitados",
        help_text="Lista de tipos de notificaciones habilitadas para este usuario"
    )
    
    # Configuración de horarios
    horario_inicio = models.TimeField(
        default='08:00',
        verbose_name="Horario de Inicio",
        help_text="Hora de inicio para recibir notificaciones"
    )
    horario_fin = models.TimeField(
        default='18:00',
        verbose_name="Horario de Fin",
        help_text="Hora de fin para recibir notificaciones"
    )
    
    # Días de la semana (0=Lunes, 6=Domingo)
    dias_habilitados = models.JSONField(
        default=default_dias_habilitados,  # Lunes a Viernes por defecto
        verbose_name="Días Habilitados",
        help_text="Lista de días de la semana habilitados (0=Lunes, 6=Domingo)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")
    
    class Meta:
        verbose_name = "Canal de Notificación"
        verbose_name_plural = "Canales de Notificación"

    def __str__(self):
        return f"Canal de {self.usuario.username}"

    def puede_recibir_notificacion(self, tipo_notificacion=None):
        """
        Verificar si el usuario puede recibir notificaciones en este momento
        """
        from datetime import datetime, time
        
        # Verificar si el tipo está habilitado
        if tipo_notificacion and self.tipos_habilitados:
            if tipo_notificacion not in self.tipos_habilitados:
                return False
        
        # Verificar horario
        now = datetime.now().time()
        if not (self.horario_inicio <= now <= self.horario_fin):
            return False
        
        # Verificar día de la semana
        today = datetime.now().weekday()  # 0=Lunes, 6=Domingo
        if today not in self.dias_habilitados:
            return False
        
        return True


class PlantillaNotificacion(models.Model):
    """
    Plantillas para diferentes tipos de notificaciones
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(
        max_length=30,
        choices=TipoNotificacion.choices,
        unique=True,
        verbose_name="Tipo"
    )
    titulo_template = models.CharField(
        max_length=200,
        verbose_name="Plantilla de Título",
        help_text="Usar {variable} para variables dinámicas"
    )
    mensaje_template = models.TextField(
        verbose_name="Plantilla de Mensaje",
        help_text="Usar {variable} para variables dinámicas"
    )
    prioridad_default = models.CharField(
        max_length=10,
        choices=PrioridadNotificacion.choices,
        default=PrioridadNotificacion.MEDIA,
        verbose_name="Prioridad por Defecto"
    )
    activa = models.BooleanField(default=True, verbose_name="Activa")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")
    
    class Meta:
        verbose_name = "Plantilla de Notificación"
        verbose_name_plural = "Plantillas de Notificación"

    def __str__(self):
        return f"Plantilla {self.get_tipo_display()}"

    def generar_contenido(self, **variables):
        """
        Generar título y mensaje usando las variables proporcionadas
        """
        try:
            titulo = self.titulo_template.format(**variables)
            mensaje = self.mensaje_template.format(**variables)
            return titulo, mensaje
        except KeyError as e:
            raise ValueError(f"Variable faltante en plantilla: {e}")


# Señales para crear canal de notificaciones automáticamente
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def crear_canal_notificaciones(sender, instance, created, **kwargs):
    """Crear canal de notificaciones para nuevos usuarios"""
    if created:
        CanalNotificacion.objects.create(
            usuario=instance,
            tipos_habilitados=[choice[0] for choice in TipoNotificacion.choices]
        )