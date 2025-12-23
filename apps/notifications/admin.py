"""
Admin para notificaciones
"""
from django.contrib import admin
from .models import Notificacion, CanalNotificacion, PlantillaNotificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    """Admin para notificaciones"""
    
    list_display = [
        'titulo', 'usuario', 'tipo', 'prioridad', 
        'leida', 'created_at', 'expires_at'
    ]
    list_filter = [
        'tipo', 'prioridad', 'leida', 'created_at', 'expires_at'
    ]
    search_fields = ['titulo', 'mensaje', 'usuario__username', 'usuario__email']
    readonly_fields = ['id', 'created_at', 'fecha_lectura']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'usuario', 'tipo', 'prioridad')
        }),
        ('Contenido', {
            'fields': ('titulo', 'mensaje', 'datos_adicionales')
        }),
        ('Estado', {
            'fields': ('leida', 'fecha_lectura', 'expires_at')
        }),
        ('Metadatos', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Filtrar por hidrológica si no es superusuario"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser or request.user.is_ente_rector:
            return qs
        
        # Solo notificaciones de la hidrológica del usuario
        return qs.filter(usuario__hidrologica=request.user.hidrologica)


@admin.register(CanalNotificacion)
class CanalNotificacionAdmin(admin.ModelAdmin):
    """Admin para canales de notificación"""
    
    list_display = [
        'usuario', 'email_habilitado', 'push_habilitado',
        'horario_inicio', 'horario_fin', 'updated_at'
    ]
    list_filter = ['email_habilitado', 'push_habilitado', 'updated_at']
    search_fields = ['usuario__username', 'usuario__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('id', 'usuario')
        }),
        ('Canales', {
            'fields': ('email_habilitado', 'push_habilitado')
        }),
        ('Configuración', {
            'fields': ('tipos_habilitados', 'horario_inicio', 'horario_fin', 'dias_habilitados')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Filtrar por hidrológica si no es superusuario"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser or request.user.is_ente_rector:
            return qs
        
        # Solo canales de la hidrológica del usuario
        return qs.filter(usuario__hidrologica=request.user.hidrologica)


@admin.register(PlantillaNotificacion)
class PlantillaNotificacionAdmin(admin.ModelAdmin):
    """Admin para plantillas de notificación"""
    
    list_display = [
        'tipo', 'titulo_template', 'prioridad_default', 
        'activa', 'updated_at'
    ]
    list_filter = ['tipo', 'prioridad_default', 'activa', 'updated_at']
    search_fields = ['titulo_template', 'mensaje_template']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'tipo', 'prioridad_default', 'activa')
        }),
        ('Plantillas', {
            'fields': ('titulo_template', 'mensaje_template'),
            'description': 'Usar {variable} para variables dinámicas'
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        """Solo superusuarios pueden crear plantillas"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Solo superusuarios pueden modificar plantillas"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Solo superusuarios pueden eliminar plantillas"""
        return request.user.is_superuser