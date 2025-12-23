"""
Tests unitarios para el sistema de permisos
"""
import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory

from apps.core.permissions import (
    IsEnteRector, IsOperadorHidrologica, IsPuntoControl,
    InventoryPermissions, MultiTenantPermission
)


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestIsEnteRectorPermission:
    """Tests para el permiso IsEnteRector"""
    
    def setup_method(self):
        self.factory = APIRequestFactory()
        self.permission = IsEnteRector()
    
    def test_admin_rector_has_permission(self, admin_rector_user):
        """Test que admin rector tenga permiso"""
        request = self.factory.get('/')
        request.user = admin_rector_user
        
        assert self.permission.has_permission(request, None) is True
    
    def test_operador_hidrologica_no_permission(self, operador_atlantico_user):
        """Test que operador hidrológica no tenga permiso"""
        request = self.factory.get('/')
        request.user = operador_atlantico_user
        
        assert self.permission.has_permission(request, None) is False
    
    def test_punto_control_no_permission(self, punto_control_user):
        """Test que punto control no tenga permiso"""
        request = self.factory.get('/')
        request.user = punto_control_user
        
        assert self.permission.has_permission(request, None) is False
    
    def test_anonymous_user_no_permission(self):
        """Test que usuario anónimo no tenga permiso"""
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        assert self.permission.has_permission(request, None) is False


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestIsOperadorHidrologicaPermission:
    """Tests para el permiso IsOperadorHidrologica"""
    
    def setup_method(self):
        self.factory = APIRequestFactory()
        self.permission = IsOperadorHidrologica()
    
    def test_operador_hidrologica_has_permission(self, operador_atlantico_user):
        """Test que operador hidrológica tenga permiso"""
        request = self.factory.get('/')
        request.user = operador_atlantico_user
        
        assert self.permission.has_permission(request, None) is True
    
    def test_admin_rector_has_permission(self, admin_rector_user):
        """Test que admin rector también tenga permiso"""
        request = self.factory.get('/')
        request.user = admin_rector_user
        
        assert self.permission.has_permission(request, None) is True
    
    def test_punto_control_no_permission(self, punto_control_user):
        """Test que punto control no tenga permiso"""
        request = self.factory.get('/')
        request.user = punto_control_user
        
        assert self.permission.has_permission(request, None) is False


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestIsPuntoControlPermission:
    """Tests para el permiso IsPuntoControl"""
    
    def setup_method(self):
        self.factory = APIRequestFactory()
        self.permission = IsPuntoControl()
    
    def test_punto_control_has_permission(self, punto_control_user):
        """Test que punto control tenga permiso"""
        request = self.factory.get('/')
        request.user = punto_control_user
        
        assert self.permission.has_permission(request, None) is True
    
    def test_admin_rector_has_permission(self, admin_rector_user):
        """Test que admin rector también tenga permiso"""
        request = self.factory.get('/')
        request.user = admin_rector_user
        
        assert self.permission.has_permission(request, None) is True
    
    def test_operador_hidrologica_no_permission(self, operador_atlantico_user):
        """Test que operador hidrológica no tenga permiso"""
        request = self.factory.get('/')
        request.user = operador_atlantico_user
        
        assert self.permission.has_permission(request, None) is False


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestInventoryPermissions:
    """Tests para los permisos de inventario"""
    
    def setup_method(self):
        self.factory = APIRequestFactory()
        self.permission = InventoryPermissions()
    
    def test_admin_rector_full_permissions(self, admin_rector_user):
        """Test que admin rector tenga permisos completos"""
        request = self.factory.get('/')
        request.user = admin_rector_user
        
        # Permisos de lectura
        assert self.permission.has_permission(request, None) is True
        
        # Permisos de escritura
        request = self.factory.post('/')
        request.user = admin_rector_user
        assert self.permission.has_permission(request, None) is True
    
    def test_operador_hidrologica_full_permissions(self, operador_atlantico_user):
        """Test que operador hidrológica tenga permisos completos"""
        request = self.factory.get('/')
        request.user = operador_atlantico_user
        
        # Permisos de lectura
        assert self.permission.has_permission(request, None) is True
        
        # Permisos de escritura
        request = self.factory.post('/')
        request.user = operador_atlantico_user
        assert self.permission.has_permission(request, None) is True
    
    def test_punto_control_read_only(self, punto_control_user):
        """Test que punto control solo tenga permisos de lectura"""
        request = self.factory.get('/')
        request.user = punto_control_user
        
        # Permisos de lectura
        assert self.permission.has_permission(request, None) is True
        
        # Sin permisos de escritura
        request = self.factory.post('/')
        request.user = punto_control_user
        assert self.permission.has_permission(request, None) is False
        
        request = self.factory.put('/')
        request.user = punto_control_user
        assert self.permission.has_permission(request, None) is False
        
        request = self.factory.delete('/')
        request.user = punto_control_user
        assert self.permission.has_permission(request, None) is False


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.permissions
class TestMultiTenantPermission:
    """Tests para el permiso de multitenencia"""
    
    def setup_method(self):
        self.factory = APIRequestFactory()
        self.permission = MultiTenantPermission()
    
    def test_authenticated_user_has_permission(self, operador_atlantico_user):
        """Test que usuario autenticado tenga permiso"""
        request = self.factory.get('/')
        request.user = operador_atlantico_user
        
        assert self.permission.has_permission(request, None) is True
    
    def test_anonymous_user_no_permission(self):
        """Test que usuario anónimo no tenga permiso"""
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        assert self.permission.has_permission(request, None) is False
    
    def test_object_permission_same_hidrologica(self, operador_atlantico_user, item_tuberia_atlantico):
        """Test permiso de objeto para misma hidrológica"""
        request = self.factory.get('/')
        request.user = operador_atlantico_user
        
        assert self.permission.has_object_permission(request, None, item_tuberia_atlantico) is True
    
    def test_object_permission_different_hidrologica(self, operador_atlantico_user, item_motor_bolivar):
        """Test permiso de objeto para diferente hidrológica"""
        request = self.factory.get('/')
        request.user = operador_atlantico_user
        
        assert self.permission.has_object_permission(request, None, item_motor_bolivar) is False
    
    def test_admin_rector_object_permission(self, admin_rector_user, item_tuberia_atlantico):
        """Test que admin rector tenga permiso sobre cualquier objeto"""
        request = self.factory.get('/')
        request.user = admin_rector_user
        
        assert self.permission.has_object_permission(request, None, item_tuberia_atlantico) is True