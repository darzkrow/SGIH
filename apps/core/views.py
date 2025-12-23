"""
Vistas para autenticación y gestión de usuarios
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .models import EnteRector, Hidrologica, Acueducto
from .serializers import (
    CustomTokenObtainPairSerializer, UserSerializer, UserCreateSerializer,
    EnteRectorSerializer, HidrologicaSerializer, AcueductoSerializer,
    HidrologicaListSerializer, AcueductoListSerializer
)
from .permissions import (
    IsEnteRector, IsOperadorHidrologica, MultiTenantPermission,
    InventoryPermissions
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para obtener tokens JWT con información del usuario
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def get_queryset(self):
        """Filtrar usuarios según el rol del usuario actual"""
        user = self.request.user
        
        if user.is_superuser or user.is_ente_rector:
            # Ente Rector puede ver todos los usuarios
            return User.objects.all()
        elif user.hidrologica:
            # Operadores solo pueden ver usuarios de su hidrológica
            return User.objects.filter(hidrologica=user.hidrologica)
        else:
            return User.objects.none()
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action == 'create':
            # Solo Ente Rector puede crear usuarios
            permission_classes = [IsEnteRector]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Solo Ente Rector puede modificar usuarios
            permission_classes = [IsEnteRector]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Obtener información del usuario actual"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Cambiar contraseña de usuario"""
        user = self.get_object()
        
        # Solo el propio usuario o Ente Rector pueden cambiar contraseña
        if user != request.user and not request.user.is_ente_rector:
            return Response(
                {'error': 'No tienes permisos para cambiar esta contraseña'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response(
                {'error': 'Se requieren old_password y new_password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.check_password(old_password):
            return Response(
                {'error': 'Contraseña actual incorrecta'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Contraseña cambiada exitosamente'})


class EnteRectorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión del Ente Rector
    """
    queryset = EnteRector.objects.all()
    serializer_class = EnteRectorSerializer
    permission_classes = [IsEnteRector]
    
    def get_permissions(self):
        """Solo lectura para operadores, escritura solo para Ente Rector"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsEnteRector]
        
        return [permission() for permission in permission_classes]


class HidrologicaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de hidrológicas
    """
    queryset = Hidrologica.objects.all()
    serializer_class = HidrologicaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return HidrologicaListSerializer
        return HidrologicaSerializer
    
    def get_queryset(self):
        """Filtrar hidrológicas según el usuario"""
        user = self.request.user
        
        if user.is_superuser or user.is_ente_rector:
            return Hidrologica.objects.all()
        elif user.hidrologica:
            # Operadores solo pueden ver su propia hidrológica
            return Hidrologica.objects.filter(id=user.hidrologica.id)
        else:
            return Hidrologica.objects.none()
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsEnteRector]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def acueductos(self, request, pk=None):
        """Obtener acueductos de una hidrológica"""
        hidrologica = self.get_object()
        acueductos = hidrologica.acueductos.filter(activo=True)
        serializer = AcueductoListSerializer(acueductos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        """Obtener estadísticas de una hidrológica"""
        hidrologica = self.get_object()
        
        # Solo Ente Rector o la propia hidrológica pueden ver estadísticas
        if not (request.user.is_ente_rector or 
                request.user.hidrologica == hidrologica):
            return Response(
                {'error': 'No tienes permisos para ver estas estadísticas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        stats = {
            'acueductos_activos': hidrologica.acueductos.filter(activo=True).count(),
            'usuarios_activos': hidrologica.usuarios.filter(is_active=True).count(),
            # Agregar más estadísticas según sea necesario
        }
        
        return Response(stats)


class AcueductoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de acueductos
    """
    queryset = Acueducto.objects.all()
    serializer_class = AcueductoSerializer
    permission_classes = [MultiTenantPermission]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AcueductoListSerializer
        return AcueductoSerializer
    
    def get_queryset(self):
        """Filtrar acueductos según el usuario"""
        user = self.request.user
        
        if user.is_superuser or user.is_ente_rector:
            return Acueducto.objects.all()
        elif user.hidrologica:
            # Operadores solo pueden ver acueductos de su hidrológica
            return Acueducto.objects.filter(hidrologica=user.hidrologica)
        else:
            return Acueducto.objects.none()
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Solo Ente Rector puede modificar acueductos
            permission_classes = [IsEnteRector]
        else:
            permission_classes = [MultiTenantPermission]
        
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Asegurar que el acueducto se cree en la hidrológica correcta"""
        # Si no es Ente Rector, forzar la hidrológica del usuario
        if not self.request.user.is_ente_rector:
            serializer.save(hidrologica=self.request.user.hidrologica)
        else:
            serializer.save()