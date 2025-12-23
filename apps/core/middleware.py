"""
Middleware para multitenencia
"""
from django.http import Http404
from django.core.exceptions import PermissionDenied
from .managers import set_tenant_context, clear_tenant_context


class MultiTenantMiddleware:
    """
    Middleware que establece el contexto de hidrológica para el usuario actual
    y maneja el filtrado automático de datos por tenant
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Limpiar contexto anterior
        clear_tenant_context()
        
        # Establecer contexto de hidrológica si el usuario está autenticado
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Establecer hidrológica del usuario en el request
            if hasattr(request.user, 'hidrologica') and request.user.hidrologica:
                request.hidrologica_id = request.user.hidrologica.id
                request.hidrologica = request.user.hidrologica
                hidrologica_id = request.user.hidrologica.id
            else:
                request.hidrologica_id = None
                request.hidrologica = None
                hidrologica_id = None
            
            # Establecer si es usuario del Ente Rector
            is_ente_rector = getattr(request.user, 'is_ente_rector', False)
            request.is_ente_rector = is_ente_rector
            
            # Establecer contexto en thread-local storage para los managers
            set_tenant_context(hidrologica_id, is_ente_rector)
        else:
            request.hidrologica_id = None
            request.hidrologica = None
            request.is_ente_rector = False
        
        try:
            response = self.get_response(request)
        finally:
            # Limpiar contexto al finalizar la request
            clear_tenant_context()
        
        return response


class TenantAccessMiddleware:
    """
    Middleware adicional para controlar acceso a recursos por tenant
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Procesar vista para validar acceso por tenant
        """
        # Solo aplicar a vistas de API autenticadas
        if (hasattr(request, 'user') and 
            request.user.is_authenticated and 
            not request.user.is_superuser and
            not getattr(request, 'is_ente_rector', False)):
            
            # Validar acceso a recursos específicos por ID
            if 'pk' in view_kwargs or 'id' in view_kwargs:
                resource_id = view_kwargs.get('pk') or view_kwargs.get('id')
                
                # Aquí se pueden agregar validaciones específicas por modelo
                # Por ahora, dejamos que los managers manejen el filtrado
                pass
        
        return None