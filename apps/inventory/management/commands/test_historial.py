"""
Comando para probar el sistema de historial de ítems
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.inventory.models import ItemInventario, EstadoItem
from apps.inventory.services import ItemHistoryService, InventoryService
from apps.core.models import Hidrologica, Acueducto

User = get_user_model()


class Command(BaseCommand):
    help = 'Probar el sistema de historial de ítems'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--item-sku',
            type=str,
            help='SKU del ítem para probar historial'
        )
        parser.add_argument(
            '--crear-eventos',
            action='store_true',
            help='Crear eventos de prueba en el historial'
        )
        parser.add_argument(
            '--mostrar-reporte',
            action='store_true',
            help='Mostrar reporte completo de trazabilidad'
        )
    
    def handle(self, *args, **options):
        item_sku = options.get('item_sku')
        crear_eventos = options.get('crear_eventos')
        mostrar_reporte = options.get('mostrar_reporte')
        
        if item_sku:
            try:
                item = ItemInventario.objects.get(sku=item_sku)
                self.probar_historial_item(item, crear_eventos, mostrar_reporte)
            except ItemInventario.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Ítem con SKU "{item_sku}" no encontrado')
                )
        else:
            self.mostrar_estadisticas_generales()
    
    def probar_historial_item(self, item, crear_eventos=False, mostrar_reporte=False):
        """Probar historial de un ítem específico"""
        self.stdout.write(
            self.style.SUCCESS(f'=== HISTORIAL DEL ÍTEM {item.sku} ===')
        )
        
        # Información básica del ítem
        self.stdout.write(f'Nombre: {item.nombre}')
        self.stdout.write(f'Tipo: {item.get_tipo_display()}')
        self.stdout.write(f'Estado actual: {item.get_estado_display()}')
        self.stdout.write(f'Ubicación: {item.ubicacion_actual}')
        
        if crear_eventos:
            self.crear_eventos_prueba(item)
        
        # Obtener historial completo
        historial = ItemHistoryService.obtener_historial_completo(item)
        
        self.stdout.write(f'\n--- HISTORIAL COMPLETO ({len(historial)} eventos) ---')
        for i, evento in enumerate(historial, 1):
            self.mostrar_evento(i, evento)
        
        if mostrar_reporte:
            self.mostrar_reporte_trazabilidad(item)
    
    def crear_eventos_prueba(self, item):
        """Crear eventos de prueba en el historial"""
        self.stdout.write(
            self.style.WARNING('Creando eventos de prueba...')
        )
        
        # Obtener usuario de prueba
        try:
            usuario = User.objects.filter(is_active=True).first()
        except:
            usuario = None
        
        # Evento de mantenimiento
        ItemHistoryService.registrar_mantenimiento(
            item=item,
            tipo_mantenimiento='Mantenimiento preventivo',
            usuario=usuario,
            observaciones='Mantenimiento de prueba creado por comando'
        )
        
        # Cambio de estado
        if item.estado != EstadoItem.MANTENIMIENTO:
            InventoryService.cambiar_estado_item(
                item=item,
                nuevo_estado=EstadoItem.MANTENIMIENTO,
                usuario=usuario,
                motivo='Prueba de cambio de estado',
                observaciones='Estado cambiado por comando de prueba'
            )
        
        # Actualización de datos
        InventoryService.actualizar_item(
            item=item,
            datos_actualizacion={
                'descripcion': f'{item.descripcion} [Actualizado por prueba]'
            },
            usuario=usuario
        )
        
        self.stdout.write(
            self.style.SUCCESS('Eventos de prueba creados exitosamente')
        )
    
    def mostrar_evento(self, numero, evento):
        """Mostrar un evento del historial"""
        fecha = evento.get('fecha', 'N/A')
        tipo = evento.get('tipo', 'N/A')
        descripcion = evento.get('descripcion', 'N/A')
        usuario_info = evento.get('usuario', {})
        usuario_nombre = usuario_info.get('username', 'Sistema') if usuario_info else 'Sistema'
        
        self.stdout.write(f'{numero}. [{fecha}] {tipo.upper()}')
        self.stdout.write(f'   Descripción: {descripcion}')
        self.stdout.write(f'   Usuario: {usuario_nombre}')
        
        # Mostrar ubicaciones si existen
        ubicacion_origen = evento.get('ubicacion_origen')
        ubicacion_destino = evento.get('ubicacion_destino')
        
        if ubicacion_origen:
            hidrologica = ubicacion_origen.get('hidrologica', {})
            acueducto = ubicacion_origen.get('acueducto', {})
            self.stdout.write(
                f'   Origen: {hidrologica.get("nombre", "N/A")} - {acueducto.get("nombre", "N/A")}'
            )
        
        if ubicacion_destino:
            hidrologica = ubicacion_destino.get('hidrologica', {})
            acueducto = ubicacion_destino.get('acueducto', {})
            self.stdout.write(
                f'   Destino: {hidrologica.get("nombre", "N/A")} - {acueducto.get("nombre", "N/A")}'
            )
        
        # Mostrar observaciones si existen
        observaciones = evento.get('observaciones')
        if observaciones:
            self.stdout.write(f'   Observaciones: {observaciones}')
        
        self.stdout.write('')  # Línea en blanco
    
    def mostrar_reporte_trazabilidad(self, item):
        """Mostrar reporte completo de trazabilidad"""
        reporte = ItemHistoryService.generar_reporte_trazabilidad(item)
        
        self.stdout.write(
            self.style.SUCCESS('\n=== REPORTE DE TRAZABILIDAD ===')
        )
        
        estadisticas = reporte['estadisticas']
        
        self.stdout.write(f'Total de eventos: {estadisticas["total_eventos"]}')
        
        # Tipos de eventos
        self.stdout.write('\n--- Tipos de eventos ---')
        for tipo, cantidad in estadisticas['tipos_eventos'].items():
            self.stdout.write(f'{tipo}: {cantidad}')
        
        # Usuarios involucrados
        self.stdout.write('\n--- Usuarios involucrados ---')
        for usuario in estadisticas['usuarios_involucrados']:
            self.stdout.write(f'- {usuario}')
        
        # Ubicaciones visitadas
        self.stdout.write('\n--- Ubicaciones visitadas ---')
        for ubicacion in estadisticas['ubicaciones_visitadas']:
            self.stdout.write(f'- {ubicacion}')
        
        # Fechas
        if estadisticas['fecha_primer_evento']:
            self.stdout.write(f'\nPrimer evento: {estadisticas["fecha_primer_evento"]}')
        if estadisticas['fecha_ultimo_evento']:
            self.stdout.write(f'Último evento: {estadisticas["fecha_ultimo_evento"]}')
    
    def mostrar_estadisticas_generales(self):
        """Mostrar estadísticas generales del sistema de historial"""
        self.stdout.write(
            self.style.SUCCESS('=== ESTADÍSTICAS DEL SISTEMA DE HISTORIAL ===')
        )
        
        # Total de ítems
        total_items = ItemInventario.objects.count()
        self.stdout.write(f'Total de ítems en el sistema: {total_items}')
        
        # Ítems con historial
        items_con_historial = ItemInventario.objects.exclude(
            historial_movimientos=[]
        ).count()
        
        self.stdout.write(f'Ítems con historial: {items_con_historial}')
        
        if total_items > 0:
            porcentaje = (items_con_historial / total_items) * 100
            self.stdout.write(f'Porcentaje con historial: {porcentaje:.1f}%')
        
        # Estadísticas por tipo de evento
        self.stdout.write('\n--- Análisis de eventos por tipo ---')
        
        tipos_eventos = {}
        total_eventos = 0
        
        for item in ItemInventario.objects.exclude(historial_movimientos=[]):
            for evento in item.historial_movimientos:
                tipo = evento.get('tipo', 'desconocido')
                tipos_eventos[tipo] = tipos_eventos.get(tipo, 0) + 1
                total_eventos += 1
        
        self.stdout.write(f'Total de eventos registrados: {total_eventos}')
        
        for tipo, cantidad in sorted(tipos_eventos.items(), key=lambda x: x[1], reverse=True):
            porcentaje = (cantidad / total_eventos * 100) if total_eventos > 0 else 0
            self.stdout.write(f'{tipo}: {cantidad} ({porcentaje:.1f}%)')
        
        # Ítems más activos
        self.stdout.write('\n--- Ítems con más actividad ---')
        
        items_actividad = []
        for item in ItemInventario.objects.exclude(historial_movimientos=[]):
            num_eventos = len(item.historial_movimientos)
            items_actividad.append((item.sku, item.nombre, num_eventos))
        
        # Ordenar por número de eventos (descendente)
        items_actividad.sort(key=lambda x: x[2], reverse=True)
        
        for i, (sku, nombre, num_eventos) in enumerate(items_actividad[:10], 1):
            self.stdout.write(f'{i}. {sku} - {nombre}: {num_eventos} eventos')
        
        self.stdout.write(
            self.style.SUCCESS('\n=== FIN DE ESTADÍSTICAS ===')
        )