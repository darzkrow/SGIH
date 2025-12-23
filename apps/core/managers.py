"""
Managers y QuerySets personalizados para multitenencia
"""
from django.db import models
from django.core.exceptions import PermissionDenied
import threading

# Thread-local storage para el contexto del tenant actual
_thread_locals = threading.local()


class TenantContext:
    """
    Contexto del tenant actual para filtrado automático
    """
    
    @classmethod
    def set_current_hidrologica(cls, hidrologica_id):
        """Establecer hidrológica actual en el contexto del thread"""
        _thread_locals.hidrologica_id = hidrologica_id
    
    @classmethod
    def get_current_hidrologica(cls):
        """Obtener hidrológica actual del contexto del thread"""
        return getattr(_thread_locals, 'hidrologica_id', None)
    
    @classmethod
    def set_is_ente_rector(cls, is_ente_rector):
        """Establecer si el usuario actual es del Ente Rector"""
        _thread_locals.is_ente_rector = is_ente_rector
    
    @classmethod
    def get_is_ente_rector(cls):
        """Verificar si el usuario actual es del Ente Rector"""
        return getattr(_thread_locals, 'is_ente_rector', False)
    
    @classmethod
    def clear(cls):
        """Limpiar contexto del thread"""
        for attr in ['hidrologica_id', 'is_ente_rector']:
            if hasattr(_thread_locals, attr):
                delattr(_thread_locals, attr)


class MultiTenantQuerySet(models.QuerySet):
    """
    QuerySet base para modelos con multitenencia
    """
    
    def for_hidrologica(self, hidrologica_id):
        """Filtrar por hidrológica específica"""
        if hidrologica_id is None:
            return self.none()
        return self.filter(hidrologica_id=hidrologica_id)
    
    def for_current_tenant(self):
        """Filtrar por el tenant actual del contexto"""
        current_hidrologica = TenantContext.get_current_hidrologica()
        if current_hidrologica is None:
            # Si no hay contexto de tenant, no mostrar nada por seguridad
            return self.none()
        return self.for_hidrologica(current_hidrologica)
    
    def global_view(self):
        """Vista global para usuarios del Ente Rector"""
        if not TenantContext.get_is_ente_rector():
            raise PermissionDenied("Solo el Ente Rector puede acceder a la vista global")
        return self.all()
    
    def anonymized_global_view(self):
        """
        Vista global anonimizada para búsquedas del Ente Rector
        Oculta información sensible de ubicación específica
        """
        if not TenantContext.get_is_ente_rector():
            raise PermissionDenied("Solo el Ente Rector puede acceder a la vista global")
        
        # Retornar queryset completo - la anonimización se hace en serializers
        return self.all()


class MultiTenantManager(models.Manager):
    """
    Manager base para modelos con multitenencia
    """
    
    def get_queryset(self):
        """
        Obtener queryset base con filtrado automático por tenant
        """
        qs = MultiTenantQuerySet(self.model, using=self._db)
        
        # Aplicar filtrado automático solo si hay contexto de tenant
        # y el usuario no es del Ente Rector
        if (not TenantContext.get_is_ente_rector() and 
            TenantContext.get_current_hidrologica() is not None):
            return qs.for_current_tenant()
        
        return qs
    
    def for_hidrologica(self, hidrologica_id):
        """Filtrar por hidrológica específica"""
        return self.get_queryset().for_hidrologica(hidrologica_id)
    
    def global_view(self):
        """Vista global para Ente Rector"""
        return MultiTenantQuerySet(self.model, using=self._db).global_view()
    
    def anonymized_global_view(self):
        """Vista global anonimizada para Ente Rector"""
        return MultiTenantQuerySet(self.model, using=self._db).anonymized_global_view()


class InventoryQuerySet(MultiTenantQuerySet):
    """
    QuerySet especializado para inventario
    """
    
    def disponibles(self):
        """Filtrar solo ítems disponibles"""
        return self.filter(estado='disponible')
    
    def por_tipo(self, tipo):
        """Filtrar por tipo de ítem"""
        return self.filter(tipo=tipo)
    
    def en_acueducto(self, acueducto_id):
        """Filtrar por acueducto específico"""
        return self.filter(acueducto_actual_id=acueducto_id)
    
    def con_stock_disponible(self):
        """Ítems con stock disponible para transferencia"""
        return self.filter(estado__in=['disponible', 'asignado'])
    
    def buscar(self, query):
        """Búsqueda por texto en múltiples campos"""
        return self.filter(
            models.Q(sku__icontains=query) |
            models.Q(nombre__icontains=query) |
            models.Q(descripcion__icontains=query)
        )


class InventoryManager(MultiTenantManager):
    """
    Manager especializado para inventario
    """
    
    def get_queryset(self):
        """Usar QuerySet especializado para inventario"""
        qs = InventoryQuerySet(self.model, using=self._db)
        
        # Aplicar filtrado automático por tenant
        if (not TenantContext.get_is_ente_rector() and 
            TenantContext.get_current_hidrologica() is not None):
            return qs.for_current_tenant()
        
        return qs
    
    def disponibles(self):
        """Ítems disponibles"""
        return self.get_queryset().disponibles()
    
    def por_tipo(self, tipo):
        """Filtrar por tipo"""
        return self.get_queryset().por_tipo(tipo)
    
    def buscar_global(self, query):
        """
        Búsqueda global para Ente Rector con resultados anonimizados
        """
        if not TenantContext.get_is_ente_rector():
            raise PermissionDenied("Solo el Ente Rector puede realizar búsquedas globales")
        
        return InventoryQuerySet(self.model, using=self._db).buscar(query)


class TransferQuerySet(MultiTenantQuerySet):
    """
    QuerySet especializado para transferencias
    """
    
    def pendientes_aprobacion(self):
        """Transferencias pendientes de aprobación"""
        return self.filter(estado='solicitada')
    
    def en_proceso(self):
        """Transferencias en proceso (aprobadas o en tránsito)"""
        return self.filter(estado__in=['aprobada', 'en_transito'])
    
    def completadas(self):
        """Transferencias completadas"""
        return self.filter(estado='completada')
    
    def por_prioridad(self, prioridad):
        """Filtrar por prioridad"""
        return self.filter(prioridad=prioridad)
    
    def involving_hidrologica(self, hidrologica_id):
        """Transferencias que involucran una hidrológica específica"""
        return self.filter(
            models.Q(hidrologica_origen_id=hidrologica_id) |
            models.Q(hidrologica_destino_id=hidrologica_id)
        )


class TransferManager(models.Manager):
    """
    Manager especializado para transferencias
    """
    
    def get_queryset(self):
        """Usar QuerySet especializado para transferencias"""
        qs = TransferQuerySet(self.model, using=self._db)
        
        # Para transferencias, mostrar las que involucran la hidrológica del usuario
        current_hidrologica = TenantContext.get_current_hidrologica()
        if (not TenantContext.get_is_ente_rector() and current_hidrologica is not None):
            return qs.involving_hidrologica(current_hidrologica)
        
        return qs
    
    def pendientes_aprobacion(self):
        """Transferencias pendientes (solo para Ente Rector)"""
        if not TenantContext.get_is_ente_rector():
            raise PermissionDenied("Solo el Ente Rector puede ver todas las transferencias pendientes")
        
        return TransferQuerySet(self.model, using=self._db).pendientes_aprobacion()
    
    def para_hidrologica(self, hidrologica_id):
        """Transferencias que involucran una hidrológica específica"""
        return TransferQuerySet(self.model, using=self._db).involving_hidrologica(hidrologica_id)


# Funciones de utilidad para establecer contexto

def set_tenant_context(hidrologica_id, is_ente_rector=False):
    """
    Establecer contexto de tenant para el thread actual
    """
    TenantContext.set_current_hidrologica(hidrologica_id)
    TenantContext.set_is_ente_rector(is_ente_rector)


def clear_tenant_context():
    """
    Limpiar contexto de tenant del thread actual
    """
    TenantContext.clear()


def with_tenant_context(hidrologica_id, is_ente_rector=False):
    """
    Decorador para establecer contexto de tenant temporalmente
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Guardar contexto actual
            old_hidrologica = TenantContext.get_current_hidrologica()
            old_is_ente_rector = TenantContext.get_is_ente_rector()
            
            try:
                # Establecer nuevo contexto
                set_tenant_context(hidrologica_id, is_ente_rector)
                return func(*args, **kwargs)
            finally:
                # Restaurar contexto anterior
                if old_hidrologica is not None:
                    set_tenant_context(old_hidrologica, old_is_ente_rector)
                else:
                    clear_tenant_context()
        
        return wrapper
    return decorator