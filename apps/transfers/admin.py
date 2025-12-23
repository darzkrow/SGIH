"""
Configuración del admin para modelos de transferencias
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import TransferenciaExterna, ItemTransferencia, MovimientoInterno


class ItemTransferenciaInline(admin.TabularInline):
    model = ItemTransferencia
    extra = 1
    fields = ['item', 'cantidad', 'observaciones']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "item":
            # Filtrar solo ítems disponibles para transferencia
            kwargs["queryset"] = db_field.related_model.objects.filter(
                estado__in=['disponible', 'asignado']
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(TransferenciaExterna)
class TransferenciaExternaAdmin(admin.ModelAdmin):
    list_display = [
        'numero_orden', 'estado_badge', 'hidrologica_origen', 'hidrologica_destino',
        'solicitado_por', 'prioridad', 'fecha_solicitud'
    ]
    list_filter = [
        'estado', 'prioridad', 'hidrologica_origen', 'hidrologica_destino',
        'fecha_solicitud', 'fecha_aprobacion'
    ]
    search_fields = [
        'numero_orden', 'motivo', 'hidrologica_origen__nombre',
        'hidrologica_destino__nombre', 'solicitado_por__username'
    ]
    readonly_fields = [
        'id', 'numero_orden', 'qr_token', 'url_firmada', 'pdf_generado',
        'fecha_solicitud', 'fecha_aprobacion', 'fecha_inicio_transito',
        'fecha_completada', 'updated_at', 'workflow_display', 'firmas_display'
    ]
    
    inlines = [ItemTransferenciaInline]
    
    fieldsets = (
        ('Información básica', {
            'fields': ('numero_orden', 'estado', 'prioridad', 'motivo', 'observaciones')
        }),
        ('Origen y Destino', {
            'fields': (
                'hidrologica_origen', 'acueducto_origen',
                'hidrologica_destino', 'acueducto_destino'
            )
        }),
        ('Usuarios', {
            'fields': ('solicitado_por', 'aprobado_por')
        }),
        ('Orden de Traspaso', {
            'fields': ('pdf_generado', 'qr_token', 'url_firmada', 'archivo_pdf'),
            'classes': ('collapse',)
        }),
        ('Workflow', {
            'fields': ('workflow_display',),
            'classes': ('collapse',)
        }),
        ('Firmas Digitales', {
            'fields': ('firmas_display',),
            'classes': ('collapse',)
        }),
        ('Información del sistema', {
            'fields': ('id', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def estado_badge(self, obj):
        """Mostrar estado con badge de color"""
        colors = {
            'solicitada': 'orange',
            'aprobada': 'blue',
            'en_transito': 'purple',
            'completada': 'green',
            'rechazada': 'red',
            'cancelada': 'gray'
        }
        color = colors.get(obj.estado, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = "Estado"
    
    def workflow_display(self, obj):
        """Mostrar timeline del workflow"""
        html = "<div style='font-family: monospace;'>"
        
        # Solicitud
        html += f"<p><strong>📝 Solicitada:</strong> {obj.fecha_solicitud.strftime('%d/%m/%Y %H:%M')}</p>"
        
        # Aprobación
        if obj.fecha_aprobacion:
            html += f"<p><strong>✅ Aprobada:</strong> {obj.fecha_aprobacion.strftime('%d/%m/%Y %H:%M')}"
            if obj.aprobado_por:
                html += f" por {obj.aprobado_por.username}"
            html += "</p>"
        
        # Tránsito
        if obj.fecha_inicio_transito:
            html += f"<p><strong>🚚 En tránsito:</strong> {obj.fecha_inicio_transito.strftime('%d/%m/%Y %H:%M')}</p>"
        
        # Completada
        if obj.fecha_completada:
            html += f"<p><strong>🎯 Completada:</strong> {obj.fecha_completada.strftime('%d/%m/%Y %H:%M')}</p>"
            if obj.duracion_proceso:
                html += f"<p><em>Duración total: {obj.duracion_proceso}</em></p>"
        
        html += "</div>"
        return format_html(html)
    workflow_display.short_description = "Timeline del Workflow"
    
    def firmas_display(self, obj):
        """Mostrar firmas digitales"""
        html = ""
        
        if obj.firma_origen:
            html += "<p><strong>🔏 Firma Origen:</strong><br>"
            html += f"Usuario: {obj.firma_origen.get('usuario', 'N/A')}<br>"
            html += f"Fecha: {obj.firma_origen.get('timestamp', 'N/A')[:19]}</p>"
        
        if obj.firma_destino:
            html += "<p><strong>🔐 Firma Destino:</strong><br>"
            html += f"Usuario: {obj.firma_destino.get('usuario', 'N/A')}<br>"
            html += f"Fecha: {obj.firma_destino.get('timestamp', 'N/A')[:19]}</p>"
        
        if not html:
            html = "<p><em>Sin firmas registradas</em></p>"
        
        return format_html(html)
    firmas_display.short_description = "Firmas Digitales"
    
    def get_queryset(self, request):
        """Filtrar por hidrológica si el usuario no es admin rector"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser or request.user.is_ente_rector:
            return qs
        elif request.user.hidrologica:
            # Mostrar transferencias donde la hidrológica del usuario esté involucrada
            return qs.filter(
                models.Q(hidrologica_origen=request.user.hidrologica) |
                models.Q(hidrologica_destino=request.user.hidrologica)
            )
        else:
            return qs.none()


@admin.register(MovimientoInterno)
class MovimientoInternoAdmin(admin.ModelAdmin):
    list_display = [
        'item', 'acueducto_origen', 'acueducto_destino',
        'usuario', 'fecha_movimiento'
    ]
    list_filter = [
        'acueducto_origen__hidrologica', 'fecha_movimiento'
    ]
    search_fields = [
        'item__sku', 'item__nombre', 'motivo',
        'acueducto_origen__nombre', 'acueducto_destino__nombre'
    ]
    readonly_fields = [
        'id', 'fecha_movimiento', 'hidrologica_display'
    ]
    
    fieldsets = (
        ('Movimiento', {
            'fields': ('item', 'acueducto_origen', 'acueducto_destino')
        }),
        ('Información', {
            'fields': ('usuario', 'motivo', 'observaciones')
        }),
        ('Sistema', {
            'fields': ('id', 'hidrologica_display', 'fecha_movimiento'),
            'classes': ('collapse',)
        }),
    )
    
    def hidrologica_display(self, obj):
        """Mostrar hidrológica del movimiento"""
        return obj.hidrologica.nombre
    hidrologica_display.short_description = "Hidrológica"
    
    def get_queryset(self, request):
        """Filtrar por hidrológica del usuario"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser or request.user.is_ente_rector:
            return qs
        elif request.user.hidrologica:
            return qs.filter(acueducto_origen__hidrologica=request.user.hidrologica)
        else:
            return qs.none()
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtrar opciones según el usuario"""
        if request.user.hidrologica and not request.user.is_superuser:
            if db_field.name in ["acueducto_origen", "acueducto_destino"]:
                kwargs["queryset"] = db_field.related_model.objects.filter(
                    hidrologica=request.user.hidrologica,
                    activo=True
                )
            elif db_field.name == "item":
                kwargs["queryset"] = db_field.related_model.objects.filter(
                    hidrologica=request.user.hidrologica
                )
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)