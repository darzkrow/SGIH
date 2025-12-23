"""
Configuración del admin para modelos organizacionales
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import EnteRector, Hidrologica, Acueducto, User


@admin.register(EnteRector)
class EnteRectorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'activo', 'created_at']
    list_filter = ['activo', 'created_at']
    search_fields = ['nombre', 'codigo']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('nombre', 'codigo', 'descripcion', 'activo')
        }),
        ('Información del sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Hidrologica)
class HidrologicaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'ente_rector', 'activa', 'created_at']
    list_filter = ['activa', 'ente_rector', 'created_at']
    search_fields = ['nombre', 'codigo']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('ente_rector', 'nombre', 'codigo', 'descripcion', 'activa')
        }),
        ('Información de contacto', {
            'fields': ('direccion', 'telefono', 'email')
        }),
        ('Información del sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Acueducto)
class AcueductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo_completo', 'hidrologica', 'activo', 'created_at']
    list_filter = ['activo', 'hidrologica', 'created_at']
    search_fields = ['nombre', 'codigo', 'hidrologica__nombre']
    readonly_fields = ['id', 'codigo_completo', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('hidrologica', 'nombre', 'codigo', 'descripcion', 'activo')
        }),
        ('Ubicación', {
            'fields': ('direccion', 'ubicacion')
        }),
        ('Información del sistema', {
            'fields': ('id', 'codigo_completo', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'rol', 'hidrologica', 'is_active', 'created_at']
    list_filter = ['rol', 'hidrologica', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información del sistema', {
            'fields': ('rol', 'hidrologica', 'telefono')
        }),
        ('Fechas importantes', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Información del sistema', {
            'fields': ('rol', 'hidrologica', 'telefono')
        }),
    )