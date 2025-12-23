"""
Serializers para transferencias
"""
from rest_framework import serializers
from .models import TransferenciaExterna, ItemTransferencia, MovimientoInterno, EstadoTransferencia
from apps.inventory.models import TipoItem
from apps.inventory.serializers import ItemInventarioListSerializer
from apps.core.serializers import HidrologicaListSerializer, AcueductoListSerializer, UserSerializer


class ItemTransferenciaSerializer(serializers.ModelSerializer):
    """
    Serializer para ítems en transferencias
    """
    item_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ItemTransferencia
        fields = ['id', 'item', 'item_info', 'cantidad', 'observaciones']
    
    def get_item_info(self, obj):
        """Información básica del ítem"""
        return {
            'id': str(obj.item.id),
            'sku': obj.item.sku,
            'nombre': obj.item.nombre,
            'tipo': obj.item.tipo,
            'tipo_display': obj.item.get_tipo_display(),
            'estado': obj.item.estado,
            'estado_display': obj.item.get_estado_display()
        }


class TransferenciaExternaListSerializer(serializers.ModelSerializer):
    """
    Serializer para lista de transferencias externas
    """
    hidrologica_origen_info = serializers.SerializerMethodField()
    hidrologica_destino_info = serializers.SerializerMethodField()
    solicitado_por_info = serializers.SerializerMethodField()
    aprobado_por_info = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TransferenciaExterna
        fields = [
            'id', 'numero_orden', 'estado', 'prioridad', 'fecha_solicitud',
            'fecha_aprobacion', 'fecha_completada', 'hidrologica_origen_info',
            'hidrologica_destino_info', 'solicitado_por_info', 'aprobado_por_info',
            'items_count', 'motivo'
        ]
    
    def get_hidrologica_origen_info(self, obj):
        """Información de hidrológica origen"""
        return {
            'id': str(obj.hidrologica_origen.id),
            'nombre': obj.hidrologica_origen.nombre,
            'codigo': obj.hidrologica_origen.codigo
        }
    
    def get_hidrologica_destino_info(self, obj):
        """Información de hidrológica destino"""
        return {
            'id': str(obj.hidrologica_destino.id),
            'nombre': obj.hidrologica_destino.nombre,
            'codigo': obj.hidrologica_destino.codigo
        }
    
    def get_solicitado_por_info(self, obj):
        """Información del usuario que solicitó"""
        return {
            'username': obj.solicitado_por.username,
            'nombre_completo': obj.solicitado_por.get_full_name()
        }
    
    def get_aprobado_por_info(self, obj):
        """Información del usuario que aprobó"""
        if obj.aprobado_por:
            return {
                'username': obj.aprobado_por.username,
                'nombre_completo': obj.aprobado_por.get_full_name()
            }
        return None
    
    def get_items_count(self, obj):
        """Cantidad de ítems en la transferencia"""
        return obj.items_transferencia.count()


class TransferenciaExternaDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para transferencias externas
    """
    hidrologica_origen_info = serializers.SerializerMethodField()
    hidrologica_destino_info = serializers.SerializerMethodField()
    acueducto_origen_info = serializers.SerializerMethodField()
    acueducto_destino_info = serializers.SerializerMethodField()
    solicitado_por_info = serializers.SerializerMethodField()
    aprobado_por_info = serializers.SerializerMethodField()
    items_transferencia = ItemTransferenciaSerializer(many=True, read_only=True)
    puede_aprobarse = serializers.ReadOnlyField()
    puede_iniciarse = serializers.ReadOnlyField()
    puede_completarse = serializers.ReadOnlyField()
    duracion_proceso = serializers.SerializerMethodField()
    
    class Meta:
        model = TransferenciaExterna
        fields = [
            'id', 'numero_orden', 'estado', 'prioridad', 'motivo', 'observaciones',
            'hidrologica_origen', 'hidrologica_origen_info', 'acueducto_origen', 'acueducto_origen_info',
            'hidrologica_destino', 'hidrologica_destino_info', 'acueducto_destino', 'acueducto_destino_info',
            'solicitado_por_info', 'aprobado_por_info', 'items_transferencia',
            'fecha_solicitud', 'fecha_aprobacion', 'fecha_inicio_transito', 'fecha_completada',
            'pdf_generado', 'qr_token', 'archivo_pdf', 'firma_origen', 'firma_destino',
            'puede_aprobarse', 'puede_iniciarse', 'puede_completarse', 'duracion_proceso',
            'updated_at'
        ]
        read_only_fields = [
            'id', 'numero_orden', 'fecha_solicitud', 'fecha_aprobacion', 
            'fecha_inicio_transito', 'fecha_completada', 'pdf_generado', 
            'qr_token', 'archivo_pdf', 'firma_origen', 'firma_destino', 'updated_at'
        ]
    
    def get_hidrologica_origen_info(self, obj):
        return {
            'id': str(obj.hidrologica_origen.id),
            'nombre': obj.hidrologica_origen.nombre,
            'codigo': obj.hidrologica_origen.codigo
        }
    
    def get_hidrologica_destino_info(self, obj):
        return {
            'id': str(obj.hidrologica_destino.id),
            'nombre': obj.hidrologica_destino.nombre,
            'codigo': obj.hidrologica_destino.codigo
        }
    
    def get_acueducto_origen_info(self, obj):
        return {
            'id': str(obj.acueducto_origen.id),
            'nombre': obj.acueducto_origen.nombre,
            'codigo': obj.acueducto_origen.codigo
        }
    
    def get_acueducto_destino_info(self, obj):
        return {
            'id': str(obj.acueducto_destino.id),
            'nombre': obj.acueducto_destino.nombre,
            'codigo': obj.acueducto_destino.codigo
        }
    
    def get_solicitado_por_info(self, obj):
        return {
            'username': obj.solicitado_por.username,
            'nombre_completo': obj.solicitado_por.get_full_name(),
            'email': obj.solicitado_por.email
        }
    
    def get_aprobado_por_info(self, obj):
        if obj.aprobado_por:
            return {
                'username': obj.aprobado_por.username,
                'nombre_completo': obj.aprobado_por.get_full_name(),
                'email': obj.aprobado_por.email
            }
        return None
    
    def get_duracion_proceso(self, obj):
        """Duración del proceso en días"""
        if obj.duracion_proceso:
            return obj.duracion_proceso.days
        return None


class TransferenciaExternaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear transferencias externas
    """
    items_solicitados = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        help_text="Lista de ítems: [{'item_id': 'uuid', 'cantidad': 1, 'observaciones': ''}]"
    )
    
    class Meta:
        model = TransferenciaExterna
        fields = [
            'hidrologica_destino', 'acueducto_destino', 'motivo', 
            'prioridad', 'observaciones', 'items_solicitados'
        ]
    
    def validate_items_solicitados(self, value):
        """Validar ítems solicitados"""
        if not value:
            raise serializers.ValidationError("Se debe solicitar al menos un ítem")
        
        from apps.inventory.models import ItemInventario
        
        for item_data in value:
            if 'item_id' not in item_data:
                raise serializers.ValidationError("Cada ítem debe tener 'item_id'")
            
            try:
                item = ItemInventario.objects.get(id=item_data['item_id'])
                if not item.puede_transferirse:
                    raise serializers.ValidationError(
                        f"El ítem {item.sku} no está disponible para transferencia"
                    )
            except ItemInventario.DoesNotExist:
                raise serializers.ValidationError(
                    f"Ítem con ID {item_data['item_id']} no encontrado"
                )
        
        return value
    
    def create(self, validated_data):
        """Crear transferencia usando el servicio"""
        from .services import TransferService
        
        items_solicitados = validated_data.pop('items_solicitados')
        user = self.context['request'].user
        
        # Usar hidrológica del usuario como origen
        hidrologica_origen = user.hidrologica
        # Por ahora usar el primer acueducto activo como origen
        acueducto_origen = hidrologica_origen.acueductos.filter(activo=True).first()
        
        transferencia = TransferService.solicitar_transferencia(
            hidrologica_origen_id=hidrologica_origen.id,
            acueducto_origen_id=acueducto_origen.id,
            hidrologica_destino_id=validated_data['hidrologica_destino'].id,
            acueducto_destino_id=validated_data['acueducto_destino'].id,
            items_solicitados=items_solicitados,
            usuario=user,
            motivo=validated_data['motivo'],
            prioridad=validated_data.get('prioridad', 'media')
        )
        
        return transferencia


class MovimientoInternoSerializer(serializers.ModelSerializer):
    """
    Serializer para movimientos internos
    """
    item_info = serializers.SerializerMethodField()
    acueducto_origen_info = serializers.SerializerMethodField()
    acueducto_destino_info = serializers.SerializerMethodField()
    usuario_info = serializers.SerializerMethodField()
    hidrologica_info = serializers.SerializerMethodField()
    
    class Meta:
        model = MovimientoInterno
        fields = [
            'id', 'item_info', 'acueducto_origen_info', 'acueducto_destino_info',
            'usuario_info', 'hidrologica_info', 'motivo', 'observaciones',
            'fecha_movimiento'
        ]
    
    def get_item_info(self, obj):
        return {
            'id': str(obj.item.id),
            'sku': obj.item.sku,
            'nombre': obj.item.nombre,
            'tipo_display': obj.item.get_tipo_display()
        }
    
    def get_acueducto_origen_info(self, obj):
        return {
            'id': str(obj.acueducto_origen.id),
            'nombre': obj.acueducto_origen.nombre,
            'codigo': obj.acueducto_origen.codigo
        }
    
    def get_acueducto_destino_info(self, obj):
        return {
            'id': str(obj.acueducto_destino.id),
            'nombre': obj.acueducto_destino.nombre,
            'codigo': obj.acueducto_destino.codigo
        }
    
    def get_usuario_info(self, obj):
        return {
            'username': obj.usuario.username,
            'nombre_completo': obj.usuario.get_full_name()
        }
    
    def get_hidrologica_info(self, obj):
        return {
            'id': str(obj.hidrologica.id),
            'nombre': obj.hidrologica.nombre,
            'codigo': obj.hidrologica.codigo
        }


class AprobacionTransferenciaSerializer(serializers.Serializer):
    """
    Serializer para aprobar/rechazar transferencias
    """
    accion = serializers.ChoiceField(choices=['aprobar', 'rechazar'])
    observaciones = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    motivo_rechazo = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate(self, attrs):
        if attrs['accion'] == 'rechazar' and not attrs.get('motivo_rechazo'):
            raise serializers.ValidationError(
                "Se requiere motivo_rechazo para rechazar una transferencia"
            )
        return attrs


class BusquedaStockSerializer(serializers.Serializer):
    """
    Serializer para búsqueda de stock disponible
    """
    tipo_item = serializers.ChoiceField(choices=[choice[0] for choice in TipoItem.choices])
    hidrologica_excluir = serializers.UUIDField(required=False)


class ConfirmacionQRSerializer(serializers.Serializer):
    """
    Serializer para confirmaciones via QR
    """
    token = serializers.CharField(max_length=255)
    accion = serializers.ChoiceField(choices=['iniciar_transito', 'completar'])
    observaciones = serializers.CharField(max_length=500, required=False, allow_blank=True)