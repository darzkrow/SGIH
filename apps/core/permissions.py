"""
Sistema de permisos basado en roles (RBAC) para la plataforma
"""
from rest_framework import permissions
from rest_framework.permissions import BasePermission
from django.core.exceptions import PermissionDenied


class IsEnteRector(BasePermission):
    """
    Permiso para usuarios del Ente Rector
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, 'is_ente_rector', False)
        )


class IsOperadorHidrologica(BasePermission):
    """
    Permiso para operadores de hidrológica
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, 'is_operador_hidrologica', False) and
            request.user.hidrologica is not None
        )


class IsPuntoControl(BasePermission):
    """
    Permiso para puntos de control
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, 'is_punto_control', False)
        )


class IsOwnerOrEnteRector(BasePermission):
    """
    Permiso para propietarios del recurso o Ente Rector
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Ente Rector tiene acceso completo
        if getattr(request.user, 'is_ente_rector', False):
            return True
        
        # Verificar si el objeto pertenece a la hidrológica del usuario
        if hasattr(obj, 'hidrologica'):
            return obj.hidrologica == request.user.hidrologica
        
        # Para objetos sin hidrológica directa, verificar relaciones
        if hasattr(obj, 'hidrologica_origen'):
            return (obj.hidrologica_origen == request.user.hidrologica or 
                   obj.hidrologica_destino == request.user.hidrologica)
        
        return False


class IsOwnerOrReadOnly(BasePermission):
    """
    Permiso para propietarios del recurso o solo lectura
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Permisos de lectura para cualquier usuario autenticado
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permisos de escritura solo para el propietario
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        
        # Para notificaciones, verificar destinatario
        if hasattr(obj, 'destinatario'):
            return obj.destinatario == request.user
        
        return False


class CanManageInventory(BasePermission):
    """
    Permiso para gestionar inventario
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Ente Rector puede ver todo (con restricciones en object_permission)
        if getattr(request.user, 'is_ente_rector', False):
            return True
        
        # Operadores pueden gestionar su inventario
        if getattr(request.user, 'is_operador_hidrologica', False):
            return request.user.hidrologica is not None
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Ente Rector tiene acceso de solo lectura para vista global
        if getattr(request.user, 'is_ente_rector', False):
            # Solo lectura para Ente Rector en inventario de otras hidrológicas
            return request.method in permissions.SAFE_METHODS
        
        # Operadores solo pueden gestionar su propio inventario
        if getattr(request.user, 'is_operador_hidrologica', False):
            return hasattr(obj, 'hidrologica') and obj.hidrologica == request.user.hidrologica
        
        return False


class CanManageTransfers(BasePermission):
    """
    Permiso para gestionar transferencias
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Todos los roles autenticados pueden ver transferencias
        return True
    
    def has_object_permission(self, request, view, obj):
        # Ente Rector puede gestionar todas las transferencias
        if getattr(request.user, 'is_ente_rector', False):
            return True
        
        # Operadores pueden gestionar transferencias que involucren su hidrológica
        if getattr(request.user, 'is_operador_hidrologica', False):
            if hasattr(obj, 'hidrologica_origen') and hasattr(obj, 'hidrologica_destino'):
                return (obj.hidrologica_origen == request.user.hidrologica or 
                       obj.hidrologica_destino == request.user.hidrologica)
        
        # Puntos de control pueden ver transferencias para validación QR
        if getattr(request.user, 'is_punto_control', False):
            return request.method in permissions.SAFE_METHODS
        
        return False


class CanApproveTransfers(BasePermission):
    """
    Permiso para aprobar transferencias (solo Ente Rector)
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, 'is_ente_rector', False)
        )


class CanValidateQR(BasePermission):
    """
    Permiso para validar códigos QR (acceso público limitado)
    """
    
    def has_permission(self, request, view):
        # Acceso público para validación de QR, pero con limitaciones
        return True
    
    def has_object_permission(self, request, view, obj):
        # Solo lectura para validación QR
        return request.method in permissions.SAFE_METHODS


class MultiTenantPermission(BasePermission):
    """
    Permiso base que respeta la multitenencia
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Verificar que el usuario tenga una hidrológica asignada
        # (excepto para Ente Rector)
        if not getattr(request.user, 'is_ente_rector', False):
            if not request.user.hidrologica:
                return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        # Ente Rector tiene acceso global
        if getattr(request.user, 'is_ente_rector', False):
            return True
        
        # Verificar que el objeto pertenezca al tenant del usuario
        if hasattr(obj, 'hidrologica'):
            return obj.hidrologica == request.user.hidrologica
        
        return False


# Combinaciones de permisos comunes

class InventoryPermissions(BasePermission):
    """
    Permisos combinados para inventario
    """
    
    def has_permission(self, request, view):
        return (
            MultiTenantPermission().has_permission(request, view) and
            CanManageInventory().has_permission(request, view)
        )
    
    def has_object_permission(self, request, view, obj):
        return (
            MultiTenantPermission().has_object_permission(request, view, obj) and
            CanManageInventory().has_object_permission(request, view, obj)
        )


class TransferPermissions(BasePermission):
    """
    Permisos combinados para transferencias
    """
    
    def has_permission(self, request, view):
        return (
            MultiTenantPermission().has_permission(request, view) and
            CanManageTransfers().has_permission(request, view)
        )
    
    def has_object_permission(self, request, view, obj):
        return (
            MultiTenantPermission().has_object_permission(request, view, obj) and
            CanManageTransfers().has_object_permission(request, view, obj)
        )


# Decoradores para vistas basadas en funciones

def require_ente_rector(view_func):
    """
    Decorador que requiere que el usuario sea del Ente Rector
    """
    def wrapper(request, *args, **kwargs):
        if not getattr(request.user, 'is_ente_rector', False):
            raise PermissionDenied("Solo el Ente Rector puede acceder a esta funcionalidad")
        return view_func(request, *args, **kwargs)
    return wrapper


def require_operador_hidrologica(view_func):
    """
    Decorador que requiere que el usuario sea operador de hidrológica
    """
    def wrapper(request, *args, **kwargs):
        if not (getattr(request.user, 'is_operador_hidrologica', False) and 
                request.user.hidrologica):
            raise PermissionDenied("Solo operadores de hidrológica pueden acceder a esta funcionalidad")
        return view_func(request, *args, **kwargs)
    return wrapper


def require_same_hidrologica(view_func):
    """
    Decorador que requiere que el recurso pertenezca a la misma hidrológica del usuario
    """
    def wrapper(request, *args, **kwargs):
        # Este decorador necesitaría lógica específica según el contexto
        # Se implementaría en las vistas específicas
        return view_func(request, *args, **kwargs)
    return wrapper