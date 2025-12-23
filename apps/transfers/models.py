"""
Modelos para gestión de transferencias y movimientos
"""
import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import Hidrologica, Acueducto, User
from apps.inventory.models import ItemInventario
from apps.core.managers import TransferManager, TransferQuerySet


class EstadoTransferencia(models.TextChoices):
    """Estados del workflow de transferencias externas"""
    SOLICITADA = 'solicitada', 'Solicitada'
    APROBADA = 'aprobada', 'Aprobada'
    EN_TRANSITO = 'en_transito', 'En Tránsito'
    COMPLETADA = 'completada', 'Completada'
    RECHAZADA = 'rechazada', 'Rechazada'
    CANCELADA = 'cancelada', 'Cancelada'


class TransferenciaExterna(models.Model):
    """
    Modelo para transferencias entre diferentes hidrológicas
    Requiere aprobación del Ente Rector y genera orden de traspaso
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_orden = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="Número de Orden"
    )
    
    # Origen y Destino
    hidrologica_origen = models.ForeignKey(
        Hidrologica, 
        on_delete=models.CASCADE, 
        related_name='transferencias_salida',
        verbose_name="Hidrológica Origen"
    )
    acueducto_origen = models.ForeignKey(
        Acueducto, 
        on_delete=models.CASCADE, 
        related_name='transferencias_salida',
        verbose_name="Acueducto Origen"
    )
    hidrologica_destino = models.ForeignKey(
        Hidrologica, 
        on_delete=models.CASCADE, 
        related_name='transferencias_entrada',
        verbose_name="Hidrológica Destino"
    )
    acueducto_destino = models.ForeignKey(
        Acueducto, 
        on_delete=models.CASCADE, 
        related_name='transferencias_entrada',
        verbose_name="Acueducto Destino"
    )
    
    # Estado y Workflow
    estado = models.CharField(
        max_length=20, 
        choices=EstadoTransferencia.choices, 
        default=EstadoTransferencia.SOLICITADA,
        verbose_name="Estado"
    )
    
    # Usuarios involucrados
    solicitado_por = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='transferencias_solicitadas',
        verbose_name="Solicitado por"
    )
    aprobado_por = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='transferencias_aprobadas',
        verbose_name="Aprobado por"
    )
    
    # Información de la solicitud
    motivo = models.TextField(verbose_name="Motivo de la transferencia")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    prioridad = models.CharField(
        max_length=10,
        choices=[
            ('baja', 'Baja'),
            ('media', 'Media'),
            ('alta', 'Alta'),
            ('urgente', 'Urgente')
        ],
        default='media',
        verbose_name="Prioridad"
    )
    
    # Orden de Traspaso y QR
    pdf_generado = models.BooleanField(default=False, verbose_name="PDF Generado")
    qr_token = models.CharField(
        max_length=255, 
        unique=True, 
        null=True, 
        blank=True,
        verbose_name="Token QR"
    )
    url_firmada = models.TextField(
        null=True, 
        blank=True,
        verbose_name="URL Firmada"
    )
    archivo_pdf = models.FileField(
        upload_to='ordenes_traspaso/',
        null=True,
        blank=True,
        verbose_name="Archivo PDF"
    )
    
    # Timestamps del workflow
    fecha_solicitud = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Fecha de Solicitud"
    )
    fecha_aprobacion = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Fecha de Aprobación"
    )
    fecha_inicio_transito = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Fecha de Inicio de Tránsito"
    )
    fecha_completada = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Fecha de Completación"
    )
    
    # Firmas Digitales
    firma_origen = models.JSONField(
        null=True, 
        blank=True,
        verbose_name="Firma Digital Origen",
        help_text="Timestamp y usuario que confirma salida"
    )
    firma_destino = models.JSONField(
        null=True, 
        blank=True,
        verbose_name="Firma Digital Destino",
        help_text="Timestamp y usuario que confirma recepción"
    )
    
    # Información adicional
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
    
    # Manager personalizado
    objects = TransferManager()

    class Meta:
        verbose_name = "Transferencia Externa"
        verbose_name_plural = "Transferencias Externas"
        ordering = ['-fecha_solicitud']
        indexes = [
            models.Index(fields=['estado', 'fecha_solicitud']),
            models.Index(fields=['hidrologica_origen', 'estado']),
            models.Index(fields=['hidrologica_destino', 'estado']),
            models.Index(fields=['qr_token']),
        ]

    def __str__(self):
        return f"Orden {self.numero_orden} - {self.hidrologica_origen} → {self.hidrologica_destino}"

    def clean(self):
        """Validaciones del modelo"""
        # No se puede transferir a la misma hidrológica
        if self.hidrologica_origen == self.hidrologica_destino:
            raise ValidationError(
                "No se puede crear una transferencia externa a la misma hidrológica"
            )
        
        # Validar que los acueductos pertenezcan a sus hidrológicas
        if self.acueducto_origen.hidrologica != self.hidrologica_origen:
            raise ValidationError(
                "El acueducto origen debe pertenecer a la hidrológica origen"
            )
        
        if self.acueducto_destino.hidrologica != self.hidrologica_destino:
            raise ValidationError(
                "El acueducto destino debe pertenecer a la hidrológica destino"
            )

    def save(self, *args, **kwargs):
        # Generar número de orden si es nuevo
        if not self.numero_orden:
            self.numero_orden = self.generar_numero_orden()
        
        self.full_clean()
        super().save(*args, **kwargs)

    def generar_numero_orden(self):
        """Generar número de orden único"""
        fecha = timezone.now()
        prefijo = f"ORD{fecha.year}{fecha.month:02d}"
        
        # Buscar el último número de la serie
        ultimo = TransferenciaExterna.objects.filter(
            numero_orden__startswith=prefijo
        ).order_by('-numero_orden').first()
        
        if ultimo:
            try:
                ultimo_num = int(ultimo.numero_orden[-4:])
                nuevo_num = ultimo_num + 1
            except ValueError:
                nuevo_num = 1
        else:
            nuevo_num = 1
        
        return f"{prefijo}{nuevo_num:04d}"

    def aprobar(self, usuario_rector):
        """Aprobar la transferencia"""
        if self.estado != EstadoTransferencia.SOLICITADA:
            raise ValidationError("Solo se pueden aprobar transferencias solicitadas")
        
        if not usuario_rector.is_ente_rector:
            raise ValidationError("Solo el Ente Rector puede aprobar transferencias")
        
        self.estado = EstadoTransferencia.APROBADA
        self.aprobado_por = usuario_rector
        self.fecha_aprobacion = timezone.now()
        self.save()

    def rechazar(self, usuario_rector, motivo=""):
        """Rechazar la transferencia"""
        if self.estado != EstadoTransferencia.SOLICITADA:
            raise ValidationError("Solo se pueden rechazar transferencias solicitadas")
        
        if not usuario_rector.is_ente_rector:
            raise ValidationError("Solo el Ente Rector puede rechazar transferencias")
        
        self.estado = EstadoTransferencia.RECHAZADA
        self.aprobado_por = usuario_rector
        self.observaciones += f"\n\nRechazada: {motivo}" if motivo else "\n\nRechazada"
        self.save()

    def iniciar_transito(self, usuario):
        """Marcar como en tránsito y firmar salida"""
        if self.estado != EstadoTransferencia.APROBADA:
            raise ValidationError("Solo se pueden poner en tránsito transferencias aprobadas")
        
        self.estado = EstadoTransferencia.EN_TRANSITO
        self.fecha_inicio_transito = timezone.now()
        self.firma_origen = {
            'usuario': usuario.username,
            'timestamp': timezone.now().isoformat(),
            'accion': 'confirmacion_salida'
        }
        self.save()

    def completar(self, usuario):
        """Completar la transferencia y firmar recepción"""
        if self.estado != EstadoTransferencia.EN_TRANSITO:
            raise ValidationError("Solo se pueden completar transferencias en tránsito")
        
        self.estado = EstadoTransferencia.COMPLETADA
        self.fecha_completada = timezone.now()
        self.firma_destino = {
            'usuario': usuario.username,
            'timestamp': timezone.now().isoformat(),
            'accion': 'confirmacion_recepcion'
        }
        self.save()

    @property
    def puede_aprobarse(self):
        """Verificar si puede aprobarse"""
        return self.estado == EstadoTransferencia.SOLICITADA

    @property
    def puede_iniciarse(self):
        """Verificar si puede iniciarse el tránsito"""
        return self.estado == EstadoTransferencia.APROBADA

    @property
    def puede_completarse(self):
        """Verificar si puede completarse"""
        return self.estado == EstadoTransferencia.EN_TRANSITO

    @property
    def duracion_proceso(self):
        """Calcular duración del proceso"""
        if self.fecha_completada:
            return self.fecha_completada - self.fecha_solicitud
        return None


class ItemTransferencia(models.Model):
    """
    Tabla intermedia para ítems en transferencias externas
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transferencia = models.ForeignKey(
        TransferenciaExterna,
        on_delete=models.CASCADE,
        related_name='items_transferencia'
    )
    item = models.ForeignKey(
        ItemInventario,
        on_delete=models.CASCADE,
        related_name='transferencias'
    )
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    
    class Meta:
        verbose_name = "Ítem de Transferencia"
        verbose_name_plural = "Ítems de Transferencia"
        unique_together = [['transferencia', 'item']]

    def __str__(self):
        return f"{self.item.sku} - {self.transferencia.numero_orden}"


class MovimientoInterno(models.Model):
    """
    Modelo para movimientos internos dentro de la misma hidrológica
    No requiere aprobación externa
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Ítem y ubicaciones
    item = models.ForeignKey(
        ItemInventario,
        on_delete=models.CASCADE,
        related_name='movimientos_internos',
        verbose_name="Ítem"
    )
    acueducto_origen = models.ForeignKey(
        Acueducto,
        on_delete=models.CASCADE,
        related_name='movimientos_salida',
        verbose_name="Acueducto Origen"
    )
    acueducto_destino = models.ForeignKey(
        Acueducto,
        on_delete=models.CASCADE,
        related_name='movimientos_entrada',
        verbose_name="Acueducto Destino"
    )
    
    # Información del movimiento
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='movimientos_realizados',
        verbose_name="Usuario"
    )
    motivo = models.TextField(verbose_name="Motivo del movimiento")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    
    # Timestamps
    fecha_movimiento = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha del Movimiento"
    )
    
    class Meta:
        verbose_name = "Movimiento Interno"
        verbose_name_plural = "Movimientos Internos"
        ordering = ['-fecha_movimiento']
        indexes = [
            models.Index(fields=['item', 'fecha_movimiento']),
            models.Index(fields=['acueducto_origen', 'fecha_movimiento']),
            models.Index(fields=['acueducto_destino', 'fecha_movimiento']),
        ]

    def __str__(self):
        return f"{self.item.sku}: {self.acueducto_origen} → {self.acueducto_destino}"

    def clean(self):
        """Validaciones del modelo"""
        # No se puede mover al mismo acueducto
        if self.acueducto_origen == self.acueducto_destino:
            raise ValidationError("No se puede mover un ítem al mismo acueducto")
        
        # Ambos acueductos deben pertenecer a la misma hidrológica
        if self.acueducto_origen.hidrologica != self.acueducto_destino.hidrologica:
            raise ValidationError(
                "Los acueductos deben pertenecer a la misma hidrológica para movimientos internos"
            )
        
        # El ítem debe estar en el acueducto origen
        if self.item.acueducto_actual != self.acueducto_origen:
            raise ValidationError(
                "El ítem debe estar ubicado en el acueducto origen"
            )
        
        # El ítem debe pertenecer a la hidrológica
        if self.item.hidrologica != self.acueducto_origen.hidrologica:
            raise ValidationError(
                "El ítem debe pertenecer a la misma hidrológica"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        
        # Actualizar ubicación del ítem
        self.item.mover_a_acueducto(
            self.acueducto_destino,
            usuario=self.usuario,
            observaciones=f"Movimiento interno: {self.motivo}"
        )
        
        super().save(*args, **kwargs)

    @property
    def hidrologica(self):
        """Hidrológica del movimiento"""
        return self.acueducto_origen.hidrologica