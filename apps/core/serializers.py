"""
Serializers para autenticación y modelos core
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from .models import User, EnteRector, Hidrologica, Acueducto


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para JWT que incluye información del usuario
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Agregar información personalizada al token
        token['rol'] = user.rol
        token['is_ente_rector'] = user.is_ente_rector
        
        if user.hidrologica:
            token['hidrologica_id'] = str(user.hidrologica.id)
            token['hidrologica_nombre'] = user.hidrologica.nombre
            token['hidrologica_codigo'] = user.hidrologica.codigo
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Agregar información del usuario a la respuesta
        user = self.user
        data.update({
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'rol': user.rol,
                'is_ente_rector': user.is_ente_rector,
                'hidrologica': {
                    'id': str(user.hidrologica.id),
                    'nombre': user.hidrologica.nombre,
                    'codigo': user.hidrologica.codigo
                } if user.hidrologica else None
            }
        })
        
        return data


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo User
    """
    hidrologica_info = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'rol', 'telefono', 'is_active', 'hidrologica', 'hidrologica_info',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_hidrologica_info(self, obj):
        """Información básica de la hidrológica"""
        if obj.hidrologica:
            return {
                'id': str(obj.hidrologica.id),
                'nombre': obj.hidrologica.nombre,
                'codigo': obj.hidrologica.codigo
            }
        return None


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear usuarios
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm', 'rol', 'hidrologica', 'telefono'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        
        # Validar rol y hidrológica
        rol = attrs.get('rol')
        hidrologica = attrs.get('hidrologica')
        
        if rol == User.RolChoices.OPERADOR_HIDROLOGICA and not hidrologica:
            raise serializers.ValidationError(
                "Los operadores de hidrológica deben tener una hidrológica asignada"
            )
        
        if rol == User.RolChoices.ADMIN_RECTOR and hidrologica:
            raise serializers.ValidationError(
                "Los administradores rectores no deben tener hidrológica asignada"
            )
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class EnteRectorSerializer(serializers.ModelSerializer):
    """
    Serializer para EnteRector
    """
    hidrologicas_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EnteRector
        fields = [
            'id', 'nombre', 'codigo', 'descripcion', 'activo',
            'hidrologicas_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_hidrologicas_count(self, obj):
        """Contar hidrológicas activas"""
        return obj.hidrologicas.filter(activa=True).count()


class HidrologicaSerializer(serializers.ModelSerializer):
    """
    Serializer para Hidrologica
    """
    ente_rector_info = serializers.SerializerMethodField()
    acueductos_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Hidrologica
        fields = [
            'id', 'nombre', 'codigo', 'descripcion', 'direccion',
            'telefono', 'email', 'activa', 'ente_rector', 'ente_rector_info',
            'acueductos_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_ente_rector_info(self, obj):
        """Información del ente rector"""
        return {
            'id': str(obj.ente_rector.id),
            'nombre': obj.ente_rector.nombre,
            'codigo': obj.ente_rector.codigo
        }
    
    def get_acueductos_count(self, obj):
        """Contar acueductos activos"""
        return obj.acueductos.filter(activo=True).count()


class AcueductoSerializer(serializers.ModelSerializer):
    """
    Serializer para Acueducto
    """
    hidrologica_info = serializers.SerializerMethodField()
    codigo_completo = serializers.ReadOnlyField()
    
    class Meta:
        model = Acueducto
        fields = [
            'id', 'nombre', 'codigo', 'codigo_completo', 'descripcion',
            'direccion', 'ubicacion', 'activo', 'hidrologica', 'hidrologica_info',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'codigo_completo', 'created_at', 'updated_at']
    
    def get_hidrologica_info(self, obj):
        """Información de la hidrológica"""
        return {
            'id': str(obj.hidrologica.id),
            'nombre': obj.hidrologica.nombre,
            'codigo': obj.hidrologica.codigo
        }


class HidrologicaListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listas de hidrológicas
    """
    
    class Meta:
        model = Hidrologica
        fields = ['id', 'nombre', 'codigo', 'activa']


class AcueductoListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listas de acueductos
    """
    
    class Meta:
        model = Acueducto
        fields = ['id', 'nombre', 'codigo', 'codigo_completo', 'activo']