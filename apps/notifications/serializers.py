"""
Serializers para notificaciones
"""
from rest_framework import serializers
from .models import Notificacion, CanalNotificacion, PlantillaNotificacion


class NotificacionSerializer(serializers.ModelSerializer):
    """Serializer para notificaciones"""
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    es_urgente = serializers.BooleanField(read_only=True)
    esta_expirada = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Notificacion
        fields = [
            'id', 'tipo', 'tipo_display', 'titulo', 'mensaje',
            'prioridad', 'prioridad_display', 'datos_adicionales',
            'leida', 'fecha_lectura', 'created_at', 'expires_at',
            'es_urgente', 'esta_expirada'
        ]
        read_only_fields = [
            'id', 'created_at', 'fecha_lectura', 'tipo_display',
            'prioridad_display', 'es_urgente', 'esta_expirada'
        ]


class NotificacionListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de notificaciones"""
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    
    class Meta:
        model = Notificacion
        fields = [
            'id', 'tipo', 'tipo_display', 'titulo', 'prioridad',
            'prioridad_display', 'leida', 'created_at'
        ]


class MarcarLeidaSerializer(serializers.Serializer):
    """Serializer para marcar notificaciones como leídas"""
    
    notificacion_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="Lista de IDs de notificaciones a marcar como leídas. Si no se proporciona, marca todas."
    )


class CanalNotificacionSerializer(serializers.ModelSerializer):
    """Serializer para configuración de canal de notificaciones"""
    
    class Meta:
        model = CanalNotificacion
        fields = [
            'id', 'email_habilitado', 'push_habilitado',
            'tipos_habilitados', 'horario_inicio', 'horario_fin',
            'dias_habilitados', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_tipos_habilitados(self, value):
        """Validar que los tipos de notificación sean válidos"""
        from .models import TipoNotificacion
        
        tipos_validos = [choice[0] for choice in TipoNotificacion.choices]
        
        for tipo in value:
            if tipo not in tipos_validos:
                raise serializers.ValidationError(
                    f"Tipo de notificación '{tipo}' no es válido. "
                    f"Tipos válidos: {tipos_validos}"
                )
        
        return value
    
    def validate_dias_habilitados(self, value):
        """Validar que los días sean válidos (0-6)"""
        for dia in value:
            if not isinstance(dia, int) or dia < 0 or dia > 6:
                raise serializers.ValidationError(
                    "Los días deben ser números enteros entre 0 (Lunes) y 6 (Domingo)"
                )
        
        return value
    
    def validate(self, attrs):
        """Validar que horario_inicio sea menor que horario_fin"""
        horario_inicio = attrs.get('horario_inicio')
        horario_fin = attrs.get('horario_fin')
        
        if horario_inicio and horario_fin and horario_inicio >= horario_fin:
            raise serializers.ValidationError(
                "El horario de inicio debe ser menor que el horario de fin"
            )
        
        return attrs


class PlantillaNotificacionSerializer(serializers.ModelSerializer):
    """Serializer para plantillas de notificación"""
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    prioridad_default_display = serializers.CharField(
        source='get_prioridad_default_display', 
        read_only=True
    )
    
    class Meta:
        model = PlantillaNotificacion
        fields = [
            'id', 'tipo', 'tipo_display', 'titulo_template',
            'mensaje_template', 'prioridad_default', 'prioridad_default_display',
            'activa', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tipo_display', 'prioridad_default_display']


class ContadorNotificacionesSerializer(serializers.Serializer):
    """Serializer para contador de notificaciones"""
    
    total = serializers.IntegerField(read_only=True)
    no_leidas = serializers.IntegerField(read_only=True)
    por_tipo = serializers.DictField(read_only=True)
    por_prioridad = serializers.DictField(read_only=True)


class EstadisticasNotificacionesSerializer(serializers.Serializer):
    """Serializer para estadísticas de notificaciones"""
    
    periodo = serializers.CharField(read_only=True)
    total_enviadas = serializers.IntegerField(read_only=True)
    total_leidas = serializers.IntegerField(read_only=True)
    porcentaje_lectura = serializers.FloatField(read_only=True)
    por_tipo = serializers.DictField(read_only=True)
    tiempo_promedio_lectura = serializers.FloatField(read_only=True, help_text="En horas")