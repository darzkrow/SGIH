"""
Configuración del admin para modelos de inventario
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import ItemInventario, CategoriaItem


@admin.register(ItemInventario)
class ItemInventarioAdmin(admin.ModelAdmin):
    list_display = [
        'sku', 'nombre', 'tipo', 'estado', 'hidrologica', 
        'acueducto_actual', 'valor_unitario', 'created_at'
    ]
    list_filter = [
        'tipo', 'estado', 'hidrologica', 'categoria', 
        'created_at', 'fecha_adquisicion'
    ]
    search_fields = ['sku', 'nombre', 'descripcion', 'proveedor']
    readonly_fields = [
        'id', 'ubicacion_actual_display', 'ficha_vida_display', 
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Información básica', {
            'fields': ('sku', 'nombre', 'tipo', 'categoria', 'descripcion', 'estado')
        }),
        ('Ubicación', {
            'fields': ('hidrologica', 'acueducto_actual', 'ubicacion_actual_display')
        }),
        ('Especificaciones', {
            'fields': ('especificaciones',),
            'classes': ('collapse',)
        }),
        ('Información financiera', {
            'fields': ('valor_unitario', 'fecha_adquisicion', 'proveedor', 'numero_factura'),
            'classes': ('collapse',)
        }),
        ('Trazabilidad', {
            'fields': ('ficha_vida_display',),
            'classes': ('collapse',)
        }),
        ('Información del sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def ubicacion_actual_display(self, obj):
        """Mostrar ubicación actual formateada"""
        ubicacion = obj.ubicacion_actual
        return format_html(
            "<strong>{}</strong><br>Acueducto: {}",
            ubicacion['hidrologica'],
            ubicacion['acueducto']
        )
    ubicacion_actual_display.short_description = "Ubicación Actual"
    
    def ficha_vida_display(self, obj):
        """Mostrar resumen de ficha de vida"""
        if not obj.historial_movimientos:
            return "Sin movimientos registrados"
        
        html = "<ul>"
        for mov in obj.ficha_vida_resumida:
            html += f"<li><strong>{mov['fecha'][:10]}</strong>: {mov['descripcion']}</li>"
        html += "</ul>"
        
        if len(obj.historial_movimientos) > 5:
            html += f"<em>... y {len(obj.historial_movimientos) - 5} movimientos más</em>"
        
        return format_html(html)
    ficha_vida_display.short_description = "Ficha de Vida (Últimos 5)"
    
    def get_queryset(self, request):
        """Filtrar por hidrológica si el usuario no es admin rector"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser or request.user.is_ente_rector:
            return qs
        elif request.user.hidrologica:
            return qs.filter(hidrologica=request.user.hidrologica)
        else:
            return qs.none()
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtrar opciones según el usuario"""
        if db_field.name == "acueducto_actual":
            if not request.user.is_superuser and request.user.hidrologica:
                kwargs["queryset"] = request.user.hidrologica.acueductos.filter(activo=True)
        
        if db_field.name == "hidrologica":
            if not request.user.is_superuser and request.user.hidrologica:
                kwargs["queryset"] = kwargs.get("queryset", db_field.related_model.objects).filter(
                    id=request.user.hidrologica.id
                )
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(CategoriaItem)
class CategoriaItemAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_item', 'activa', 'created_at']
    list_filter = ['tipo_item', 'activa', 'created_at']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        (None, {
            'fields': ('nombre', 'tipo_item', 'descripcion', 'activa')
        }),
        ('Información del sistema', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )