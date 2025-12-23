"""
Serializers para inventario
"""
from rest_framework import serializers
from .models import ItemInventario, CategoriaItem, TipoItem, EstadoItem
from apps.core.serializers import HidrologicaListSerializer, AcueductoListSerializer


class CategoriaItemSerializer(serializers.ModelSerializer):
    """
    Serializer para categorías de ítems
    """
    
    class Meta:
        model = CategoriaItem
        fields = [
            'id', 'nombre', 'descripcion', 'tipo_item', 'activa', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ItemInventarioListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listas de inventario
    """
    hidrologica_info = serializers.SerializerMethodField()
    acueducto_info = serializers.SerializerMethodField()
    categoria_info = serializers.SerializerMethodField()
    ubicacion_actual = serializers.ReadOnlyField()
    
    class Meta:
        model = ItemInventario
        fields = [
            'id', 'sku', 'nombre', 'tipo', 'estado', 'valor_unitario',
            'hidrologica_info', 'acueducto_info', 'categoria_info',
            'ubicacion_actual', 'created_at'
        ]
    
    def get_hidrologica_info(self, obj):
        """Información básica de hidrológica"""
        # Para Ente Rector, mostrar info completa
        # Para operadores, solo mostrar si es su hidrológica
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if (request.user.is_ente_rector or 
                (request.user.hidrologica and request.user.hidrologica == obj.hidrologica)):
                return {
                    'id': str(obj.hidrologica.id),
                    'nombre': obj.hidrologica.nombre,
                    'codigo': obj.hidrologica.codigo
                }
        
        # Vista anonimizada para búsqueda global
        return {
            'id': str(obj.hidrologica.id),
            'nombre': f"Hidrológica {obj.hidrologica.codigo}",
            'codigo': obj.hidrologica.codigo
        }
    
    def get_acueducto_info(self, obj):
        """Información básica de acueducto"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if (request.user.is_ente_rector or 
                (request.user.hidrologica and request.user.hidrologica == obj.hidrologica)):
                return {
                    'id': str(obj.acueducto_actual.id),
                    'nombre': obj.acueducto_actual.nombre,
                    'codigo': obj.acueducto_actual.codigo
                }
        
        # Vista anonimizada
        return {
            'id': str(obj.acueducto_actual.id),
            'nombre': f"Acueducto {obj.acueducto_actual.codigo}",
            'codigo': obj.acueducto_actual.codigo
        }
    
    def get_categoria_info(self, obj):
        """Información de categoría"""
        if obj.categoria:
            return {
                'id': str(obj.categoria.id),
                'nombre': obj.categoria.nombre,
                'tipo_item': obj.categoria.tipo_item
            }
        return None


class ItemInventarioDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para ítems de inventario
    """
    hidrologica_info = serializers.SerializerMethodField()
    acueducto_info = serializers.SerializerMethodField()
    categoria_info = serializers.SerializerMethodField()
    ubicacion_actual = serializers.ReadOnlyField()
    ficha_vida_resumida = serializers.ReadOnlyField()
    esta_disponible = serializers.ReadOnlyField()
    puede_transferirse = serializers.ReadOnlyField()
    
    class Meta:
        model = ItemInventario
        fields = [
            'id', 'sku', 'tipo', 'nombre', 'descripcion', 'estado',
            'hidrologica', 'hidrologica_info', 'acueducto_actual', 'acueducto_info',
            'categoria', 'categoria_info', 'especificaciones',
            'valor_unitario', 'fecha_adquisicion', 'proveedor', 'numero_factura',
            'ubicacion_actual', 'ficha_vida_resumida', 'esta_disponible', 'puede_transferirse',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'ubicacion_actual', 'ficha_vida_resumida', 'esta_disponible', 
            'puede_transferirse', 'created_at', 'updated_at'
        ]
    
    def get_hidrologica_info(self, obj):
        """Información completa de hidrológica para vista detallada"""
        return {
            'id': str(obj.hidrologica.id),
            'nombre': obj.hidrologica.nombre,
            'codigo': obj.hidrologica.codigo
        }
    
    def get_acueducto_info(self, obj):
        """Información completa de acueducto para vista detallada"""
        return {
            'id': str(obj.acueducto_actual.id),
            'nombre': obj.acueducto_actual.nombre,
            'codigo': obj.acueducto_actual.codigo,
            'codigo_completo': obj.acueducto_actual.codigo_completo
        }
    
    def get_categoria_info(self, obj):
        """Información completa de categoría"""
        if obj.categoria:
            return {
                'id': str(obj.categoria.id),
                'nombre': obj.categoria.nombre,
                'descripcion': obj.categoria.descripcion,
                'tipo_item': obj.categoria.tipo_item
            }
        return None
    
    def validate(self, attrs):
        """Validaciones del serializer"""
        # Validar que el acueducto pertenezca a la hidrológica
        acueducto_actual = attrs.get('acueducto_actual')
        hidrologica = attrs.get('hidrologica')
        
        if acueducto_actual and hidrologica:
            if acueducto_actual.hidrologica != hidrologica:
                raise serializers.ValidationError(
                    "El acueducto debe pertenecer a la hidrológica seleccionada"
                )
        
        # Validar que la categoría sea compatible con el tipo
        categoria = attrs.get('categoria')
        tipo = attrs.get('tipo')
        
        if categoria and tipo:
            if categoria.tipo_item != tipo:
                raise serializers.ValidationError(
                    "La categoría debe ser compatible con el tipo de ítem"
                )
        
        return attrs


class ItemInventarioCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear ítems de inventario
    """
    
    class Meta:
        model = ItemInventario
        fields = [
            'sku', 'tipo', 'nombre', 'descripcion', 'hidrologica', 
            'acueducto_actual', 'categoria', 'especificaciones',
            'valor_unitario', 'fecha_adquisicion', 'proveedor', 'numero_factura'
        ]
    
    def validate_sku(self, value):
        """Validar unicidad del SKU"""
        if ItemInventario.objects.filter(sku=value).exists():
            raise serializers.ValidationError("Ya existe un ítem con este SKU")
        return value
    
    def validate(self, attrs):
        """Validaciones del serializer"""
        # Validar que el acueducto pertenezca a la hidrológica
        acueducto_actual = attrs.get('acueducto_actual')
        hidrologica = attrs.get('hidrologica')
        
        if acueducto_actual.hidrologica != hidrologica:
            raise serializers.ValidationError(
                "El acueducto debe pertenecer a la hidrológica seleccionada"
            )
        
        return attrs
    
    def create(self, validated_data):
        """Crear ítem con ficha de vida inicializada"""
        item = ItemInventario.objects.create(**validated_data)
        return item


class MovimientoInternoSerializer(serializers.Serializer):
    """
    Serializer para movimientos internos
    """
    acueducto_destino_id = serializers.UUIDField()
    motivo = serializers.CharField(max_length=500)
    observaciones = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    
    def validate_acueducto_destino_id(self, value):
        """Validar que el acueducto destino exista"""
        from apps.core.models import Acueducto
        try:
            acueducto = Acueducto.objects.get(id=value)
            return value
        except Acueducto.DoesNotExist:
            raise serializers.ValidationError("Acueducto destino no encontrado")


class BusquedaGlobalSerializer(serializers.Serializer):
    """
    Serializer para búsqueda global del Ente Rector
    """
    query = serializers.CharField(max_length=200)
    tipo = serializers.ChoiceField(choices=TipoItem.choices, required=False)
    estado = serializers.ChoiceField(choices=EstadoItem.choices, required=False)
    hidrologica_id = serializers.UUIDField(required=False)
    
    def validate_query(self, value):
        """Validar que la consulta tenga al menos 3 caracteres"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("La búsqueda debe tener al menos 3 caracteres")
        return value.strip()


class EstadisticasInventarioSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de inventario
    """
    total_items = serializers.IntegerField()
    por_tipo = serializers.DictField()
    por_estado = serializers.DictField()
    valor_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    items_disponibles = serializers.IntegerField()
    items_en_transito = serializers.IntegerField()
    
    # Estadísticas por acueducto (solo para operadores)
    por_acueducto = serializers.DictField(required=False)
    
    # Estadísticas globales (solo para Ente Rector)
    por_hidrologica = serializers.DictField(required=False)


class ItemHistorialEventoSerializer(serializers.Serializer):
    """
    Serializer para eventos del historial de ítems
    """
    id = serializers.UUIDField(read_only=True)
    tipo = serializers.CharField(read_only=True)
    fecha = serializers.DateTimeField(read_only=True)
    timestamp = serializers.FloatField(read_only=True)
    descripcion = serializers.CharField(read_only=True)
    usuario = serializers.DictField(read_only=True)
    ubicacion_origen = serializers.DictField(read_only=True, allow_null=True)
    ubicacion_destino = serializers.DictField(read_only=True, allow_null=True)
    estado_anterior = serializers.CharField(read_only=True, allow_null=True)
    datos_adicionales = serializers.DictField(read_only=True)
    observaciones = serializers.CharField(read_only=True)
    metadata = serializers.DictField(read_only=True)


class ItemHistorialSerializer(serializers.Serializer):
    """
    Serializer para historial completo de ítems
    """
    item_id = serializers.UUIDField(read_only=True)
    item_sku = serializers.CharField(read_only=True)
    total_eventos = serializers.IntegerField(read_only=True)
    historial = ItemHistorialEventoSerializer(many=True, read_only=True)


class ItemTrazabilidadSerializer(serializers.Serializer):
    """
    Serializer para reporte de trazabilidad de ítems
    """
    item = serializers.DictField(read_only=True)
    estadisticas = serializers.DictField(read_only=True)
    historial_completo = ItemHistorialEventoSerializer(many=True, read_only=True)


class RegistrarMantenimientoSerializer(serializers.Serializer):
    """
    Serializer para registrar eventos de mantenimiento
    """
    tipo_mantenimiento = serializers.CharField(max_length=100)
    observaciones = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    fecha_inicio = serializers.DateTimeField(required=False, allow_null=True)
    fecha_fin = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate(self, attrs):
        """Validar fechas de mantenimiento"""
        fecha_inicio = attrs.get('fecha_inicio')
        fecha_fin = attrs.get('fecha_fin')
        
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise serializers.ValidationError(
                "La fecha de inicio no puede ser posterior a la fecha de fin"
            )
        
        return attrs


class CambiarEstadoSerializer(serializers.Serializer):
    """
    Serializer para cambiar estado de ítems
    """
    estado = serializers.ChoiceField(choices=EstadoItem.choices)
    motivo = serializers.CharField(max_length=500, required=False, allow_blank=True)
    observaciones = serializers.CharField(max_length=1000, required=False, allow_blank=True)


class FiltroHistorialSerializer(serializers.Serializer):
    """
    Serializer para filtros de historial
    """
    tipo = serializers.CharField(required=False)
    fecha_desde = serializers.DateTimeField(required=False)
    fecha_hasta = serializers.DateTimeField(required=False)
    usuario_id = serializers.UUIDField(required=False)
    
    def validate(self, attrs):
        """Validar rango de fechas"""
        fecha_desde = attrs.get('fecha_desde')
        fecha_hasta = attrs.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise serializers.ValidationError(
                "La fecha desde no puede ser posterior a la fecha hasta"
            )
        
        return attrs