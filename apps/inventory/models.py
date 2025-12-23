"""
Modelos para gestión de inventario
"""
import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import Hidrologica, Acueducto, User
from apps.core.managers import InventoryManager, InventoryQuerySet


class TipoItem(models.TextChoices):
    """Tipos de ítems de inventario"""
    TUBERIA = 'tuberia', 'Tubería'
    MOTOR = 'motor', 'Motor'
    VALVULA = 'valvula', 'Válvula'
    QUIMICO = 'quimico', 'Químico'


class EstadoItem(models.TextChoices):
    """Estados de ítems de inventario"""
    DISPONIBLE = 'disponible', 'Disponible'
    EN_TRANSITO = 'en_transito', 'En Tránsito'
    ASIGNADO = 'asignado', 'Asignado'
    MANTENIMIENTO = 'mantenimiento', 'En Mantenimiento'
    DADO_BAJA = 'dado_baja', 'Dado de Baja'


class MultiTenantQuerySet(InventoryQuerySet):
    """QuerySet personalizado para multitenencia - usar el del core"""
    pass


class MultiTenantManager(InventoryManager):
    """Manager personalizado para multitenencia - usar el del core"""
    pass


class ItemInventario(models.Model):
    """
    Modelo principal para ítems de inventario con trazabilidad completa
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU")
    tipo = models.CharField(
        max_length=20, 
        choices=TipoItem.choices, 
        verbose_name="Tipo"
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    descripcion = models.TextField(verbose_name="Descripción")
    estado = models.CharField(
        max_length=20, 
        choices=EstadoItem.choices, 
        default=EstadoItem.DISPONIBLE,
        verbose_name="Estado"
    )
    
    # Multitenencia
    hidrologica = models.ForeignKey(
        Hidrologica, 
        on_delete=models.CASCADE,
        related_name='items_inventario',
        verbose_name="Hidrológica"
    )
    acueducto_actual = models.ForeignKey(
        Acueducto, 
        on_delete=models.CASCADE,
        related_name='items_inventario',
        verbose_name="Acueducto Actual"
    )
    
    # Ficha de Vida - Historial completo de movimientos
    historial_movimientos = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Historial de Movimientos",
        help_text="Ficha de vida completa del ítem"
    )
    
    # Especificaciones técnicas del ítem
    especificaciones = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Especificaciones Técnicas",
        help_text="Características técnicas específicas del ítem"
    )
    
    # Información financiera
    valor_unitario = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Valor Unitario"
    )
    fecha_adquisicion = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Fecha de Adquisición"
    )
    
    # Información de proveedor
    proveedor = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name="Proveedor"
    )
    numero_factura = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name="Número de Factura"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    
    # Managers
    objects = InventoryManager()
    
    class Meta:
        verbose_name = "Ítem de Inventario"
        verbose_name_plural = "Ítems de Inventario"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['hidrologica', 'tipo']),
            models.Index(fields=['hidrologica', 'estado']),
            models.Index(fields=['sku']),
            models.Index(fields=['acueducto_actual']),
        ]

    def __str__(self):
        return f"{self.sku} - {self.nombre}"

    def clean(self):
        """Validaciones del modelo"""
        # Validar que el acueducto pertenezca a la hidrológica
        if self.acueducto_actual and self.hidrologica:
            if self.acueducto_actual.hidrologica != self.hidrologica:
                raise ValidationError(
                    "El acueducto debe pertenecer a la hidrológica seleccionada"
                )

    def save(self, *args, **kwargs):
        # Verificar si es una creación o actualización
        is_new = not self.pk
        
        # Si es nuevo, inicializar ficha de vida básica
        if is_new and not self.historial_movimientos:
            self.historial_movimientos = []
        
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Si es nuevo, registrar evento de creación usando el servicio
        if is_new:
            from .services import ItemHistoryService
            ItemHistoryService.registrar_creacion(self)

    def inicializar_ficha_vida(self):
        """Inicializar la ficha de vida del ítem"""
        self.historial_movimientos = [{
            'tipo': 'creacion',
            'fecha': timezone.now().isoformat(),
            'descripcion': 'Ítem creado en el sistema',
            'ubicacion_origen': None,
            'ubicacion_destino': {
                'hidrologica': self.hidrologica.nombre,
                'acueducto': self.acueducto_actual.nombre if self.acueducto_actual else None
            },
            'usuario': None,
            'observaciones': f'Ítem {self.sku} registrado inicialmente'
        }]

    def agregar_movimiento(self, tipo, descripcion, ubicacion_origen=None, 
                          ubicacion_destino=None, usuario=None, observaciones=""):
        """
        Agregar un movimiento al historial de la ficha de vida
        """
        movimiento = {
            'tipo': tipo,
            'fecha': timezone.now().isoformat(),
            'descripcion': descripcion,
            'ubicacion_origen': ubicacion_origen,
            'ubicacion_destino': ubicacion_destino,
            'usuario': usuario.username if usuario else None,
            'observaciones': observaciones
        }
        
        if not self.historial_movimientos:
            self.historial_movimientos = []
        
        self.historial_movimientos.append(movimiento)
        self.save(update_fields=['historial_movimientos', 'updated_at'])

    def cambiar_estado(self, nuevo_estado, usuario=None, observaciones=""):
        """Cambiar estado del ítem y registrar en historial usando el servicio"""
        from .services import ItemHistoryService
        
        estado_anterior = self.estado
        self.estado = nuevo_estado
        self.save(update_fields=['estado', 'updated_at'])
        
        ItemHistoryService.registrar_cambio_estado(
            item=self,
            estado_anterior=estado_anterior,
            nuevo_estado=nuevo_estado,
            usuario=usuario,
            observaciones=observaciones
        )

    def mover_a_acueducto(self, nuevo_acueducto, usuario=None, observaciones=""):
        """Mover ítem a otro acueducto y registrar en historial usando el servicio"""
        from .services import ItemHistoryService
        
        acueducto_anterior = self.acueducto_actual
        
        # Validar que el nuevo acueducto pertenezca a la misma hidrológica
        if nuevo_acueducto.hidrologica != self.hidrologica:
            raise ValidationError(
                "No se puede mover a un acueducto de otra hidrológica"
            )
        
        self.acueducto_actual = nuevo_acueducto
        self.save(update_fields=['acueducto_actual', 'updated_at'])
        
        ItemHistoryService.registrar_movimiento_interno(
            item=self,
            acueducto_origen=acueducto_anterior,
            acueducto_destino=nuevo_acueducto,
            usuario=usuario,
            observaciones=observaciones
        )

    @property
    def ficha_vida_resumida(self):
        """Resumen de la ficha de vida para mostrar en APIs"""
        from .services import ItemHistoryService
        
        historial = ItemHistoryService.obtener_historial_completo(self)
        
        return [{
            'fecha': evento['fecha'],
            'tipo': evento['tipo'],
            'descripcion': evento['descripcion'],
            'usuario': evento.get('usuario', {}).get('username')
        } for evento in historial[:5]]  # Últimos 5 eventos
    
    @property
    def ficha_vida_completa(self):
        """Ficha de vida completa usando el servicio de historial"""
        from .services import ItemHistoryService
        return ItemHistoryService.obtener_historial_completo(self)
    
    def obtener_reporte_trazabilidad(self):
        """Obtener reporte completo de trazabilidad"""
        from .services import ItemHistoryService
        return ItemHistoryService.generar_reporte_trazabilidad(self)

    @property
    def ubicacion_actual(self):
        """Ubicación actual del ítem"""
        return {
            'hidrologica': self.hidrologica.nombre,
            'hidrologica_codigo': self.hidrologica.codigo,
            'acueducto': self.acueducto_actual.nombre,
            'acueducto_codigo': self.acueducto_actual.codigo
        }

    @property
    def esta_disponible(self):
        """Verificar si el ítem está disponible"""
        return self.estado == EstadoItem.DISPONIBLE

    @property
    def puede_transferirse(self):
        """Verificar si el ítem puede ser transferido"""
        return self.estado in [EstadoItem.DISPONIBLE, EstadoItem.ASIGNADO]


class CategoriaItem(models.Model):
    """
    Categorías adicionales para clasificar ítems
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    tipo_item = models.CharField(
        max_length=20, 
        choices=TipoItem.choices,
        verbose_name="Tipo de Ítem"
    )
    activa = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        verbose_name = "Categoría de Ítem"
        verbose_name_plural = "Categorías de Ítems"
        ordering = ['tipo_item', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_item_display()})"


# Agregar relación de categoría al ItemInventario
ItemInventario.add_to_class(
    'categoria',
    models.ForeignKey(
        CategoriaItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items',
        verbose_name="Categoría"
    )
)