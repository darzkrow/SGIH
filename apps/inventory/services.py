"""
Servicios para gestión de inventario y trazabilidad
"""
import uuid
from datetime import datetime
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import ItemInventario, EstadoItem, TipoItem

User = get_user_model()


class ItemHistoryService:
    """
    Servicio para gestión del historial y trazabilidad de ítems
    """
    
    # Tipos de eventos para el historial
    EVENTO_CREACION = 'creacion'
    EVENTO_CAMBIO_ESTADO = 'cambio_estado'
    EVENTO_MOVIMIENTO_INTERNO = 'movimiento_interno'
    EVENTO_TRANSFERENCIA_EXTERNA = 'transferencia_externa'
    EVENTO_MANTENIMIENTO = 'mantenimiento'
    EVENTO_ACTUALIZACION = 'actualizacion'
    EVENTO_ASIGNACION = 'asignacion'
    EVENTO_LIBERACION = 'liberacion'
    
    @staticmethod
    def registrar_evento(item, tipo_evento, descripcion, usuario=None, 
                        ubicacion_origen=None, ubicacion_destino=None, 
                        datos_adicionales=None, observaciones=""):
        """
        Registrar un evento en el historial del ítem
        
        Args:
            item: ItemInventario instance
            tipo_evento: Tipo de evento (usar constantes de la clase)
            descripcion: Descripción del evento
            usuario: Usuario que ejecuta la acción
            ubicacion_origen: Ubicación origen (dict)
            ubicacion_destino: Ubicación destino (dict)
            datos_adicionales: Datos adicionales del evento (dict)
            observaciones: Observaciones adicionales
        """
        evento = {
            'id': str(uuid.uuid4()),
            'tipo': tipo_evento,
            'fecha': timezone.now().isoformat(),
            'timestamp': timezone.now().timestamp(),
            'descripcion': descripcion,
            'usuario': {
                'id': str(usuario.id) if usuario else None,
                'username': usuario.username if usuario else None,
                'nombre_completo': usuario.get_full_name() if usuario else None,
                'rol': usuario.rol if usuario else None
            } if usuario else None,
            'ubicacion_origen': ubicacion_origen,
            'ubicacion_destino': ubicacion_destino,
            'estado_anterior': item.estado,
            'datos_adicionales': datos_adicionales or {},
            'observaciones': observaciones,
            'metadata': {
                'ip_address': None,  # Se puede agregar desde la vista
                'user_agent': None,  # Se puede agregar desde la vista
                'session_id': None   # Se puede agregar desde la vista
            }
        }
        
        # Inicializar historial si no existe
        if not item.historial_movimientos:
            item.historial_movimientos = []
        
        # Agregar evento al historial
        item.historial_movimientos.append(evento)
        
        # Guardar solo el campo de historial para optimizar
        item.save(update_fields=['historial_movimientos', 'updated_at'])
        
        return evento
    
    @staticmethod
    def registrar_creacion(item, usuario=None, observaciones=""):
        """Registrar creación del ítem"""
        return ItemHistoryService.registrar_evento(
            item=item,
            tipo_evento=ItemHistoryService.EVENTO_CREACION,
            descripcion=f'Ítem {item.sku} creado en el sistema',
            usuario=usuario,
            ubicacion_destino={
                'hidrologica': {
                    'id': str(item.hidrologica.id),
                    'nombre': item.hidrologica.nombre,
                    'codigo': item.hidrologica.codigo
                },
                'acueducto': {
                    'id': str(item.acueducto_actual.id),
                    'nombre': item.acueducto_actual.nombre,
                    'codigo': item.acueducto_actual.codigo
                } if item.acueducto_actual else None
            },
            datos_adicionales={
                'tipo_item': item.tipo,
                'valor_unitario': float(item.valor_unitario) if item.valor_unitario else None,
                'proveedor': item.proveedor,
                'numero_factura': item.numero_factura
            },
            observaciones=observaciones
        )
    
    @staticmethod
    def registrar_cambio_estado(item, estado_anterior, nuevo_estado, usuario=None, 
                               motivo="", observaciones=""):
        """Registrar cambio de estado del ítem"""
        return ItemHistoryService.registrar_evento(
            item=item,
            tipo_evento=ItemHistoryService.EVENTO_CAMBIO_ESTADO,
            descripcion=f'Estado cambiado de {estado_anterior} a {nuevo_estado}',
            usuario=usuario,
            datos_adicionales={
                'estado_anterior': estado_anterior,
                'estado_nuevo': nuevo_estado,
                'motivo': motivo
            },
            observaciones=observaciones
        )
    
    @staticmethod
    def registrar_movimiento_interno(item, acueducto_origen, acueducto_destino, 
                                   usuario=None, motivo="", observaciones=""):
        """Registrar movimiento interno del ítem"""
        return ItemHistoryService.registrar_evento(
            item=item,
            tipo_evento=ItemHistoryService.EVENTO_MOVIMIENTO_INTERNO,
            descripcion=f'Movimiento interno de {acueducto_origen.nombre} a {acueducto_destino.nombre}',
            usuario=usuario,
            ubicacion_origen={
                'hidrologica': {
                    'id': str(item.hidrologica.id),
                    'nombre': item.hidrologica.nombre,
                    'codigo': item.hidrologica.codigo
                },
                'acueducto': {
                    'id': str(acueducto_origen.id),
                    'nombre': acueducto_origen.nombre,
                    'codigo': acueducto_origen.codigo
                }
            },
            ubicacion_destino={
                'hidrologica': {
                    'id': str(item.hidrologica.id),
                    'nombre': item.hidrologica.nombre,
                    'codigo': item.hidrologica.codigo
                },
                'acueducto': {
                    'id': str(acueducto_destino.id),
                    'nombre': acueducto_destino.nombre,
                    'codigo': acueducto_destino.codigo
                }
            },
            datos_adicionales={
                'motivo': motivo,
                'tipo_movimiento': 'interno'
            },
            observaciones=observaciones
        )
    
    @staticmethod
    def registrar_transferencia_externa(item, hidrologica_origen, hidrologica_destino,
                                      acueducto_origen, acueducto_destino, 
                                      numero_orden, usuario=None, observaciones=""):
        """Registrar transferencia externa del ítem"""
        return ItemHistoryService.registrar_evento(
            item=item,
            tipo_evento=ItemHistoryService.EVENTO_TRANSFERENCIA_EXTERNA,
            descripcion=f'Transferencia externa de {hidrologica_origen.nombre} a {hidrologica_destino.nombre}',
            usuario=usuario,
            ubicacion_origen={
                'hidrologica': {
                    'id': str(hidrologica_origen.id),
                    'nombre': hidrologica_origen.nombre,
                    'codigo': hidrologica_origen.codigo
                },
                'acueducto': {
                    'id': str(acueducto_origen.id),
                    'nombre': acueducto_origen.nombre,
                    'codigo': acueducto_origen.codigo
                }
            },
            ubicacion_destino={
                'hidrologica': {
                    'id': str(hidrologica_destino.id),
                    'nombre': hidrologica_destino.nombre,
                    'codigo': hidrologica_destino.codigo
                },
                'acueducto': {
                    'id': str(acueducto_destino.id),
                    'nombre': acueducto_destino.nombre,
                    'codigo': acueducto_destino.codigo
                }
            },
            datos_adicionales={
                'numero_orden': numero_orden,
                'tipo_movimiento': 'externo'
            },
            observaciones=observaciones
        )
    
    @staticmethod
    def registrar_mantenimiento(item, tipo_mantenimiento, usuario=None, 
                              fecha_inicio=None, fecha_fin=None, observaciones=""):
        """Registrar evento de mantenimiento del ítem"""
        return ItemHistoryService.registrar_evento(
            item=item,
            tipo_evento=ItemHistoryService.EVENTO_MANTENIMIENTO,
            descripcion=f'Mantenimiento {tipo_mantenimiento} realizado',
            usuario=usuario,
            datos_adicionales={
                'tipo_mantenimiento': tipo_mantenimiento,
                'fecha_inicio': fecha_inicio.isoformat() if fecha_inicio else None,
                'fecha_fin': fecha_fin.isoformat() if fecha_fin else None
            },
            observaciones=observaciones
        )
    
    @staticmethod
    def registrar_actualizacion(item, campos_modificados, usuario=None, observaciones=""):
        """Registrar actualización de datos del ítem"""
        return ItemHistoryService.registrar_evento(
            item=item,
            tipo_evento=ItemHistoryService.EVENTO_ACTUALIZACION,
            descripcion=f'Datos del ítem actualizados: {", ".join(campos_modificados)}',
            usuario=usuario,
            datos_adicionales={
                'campos_modificados': campos_modificados
            },
            observaciones=observaciones
        )
    
    @staticmethod
    def obtener_historial_completo(item):
        """Obtener historial completo del ítem ordenado por fecha"""
        if not item.historial_movimientos:
            return []
        
        # Ordenar por timestamp (más reciente primero)
        historial = sorted(
            item.historial_movimientos,
            key=lambda x: x.get('timestamp', 0),
            reverse=True
        )
        
        return historial
    
    @staticmethod
    def obtener_historial_por_tipo(item, tipo_evento):
        """Obtener historial filtrado por tipo de evento"""
        historial = ItemHistoryService.obtener_historial_completo(item)
        return [evento for evento in historial if evento.get('tipo') == tipo_evento]
    
    @staticmethod
    def obtener_historial_por_usuario(item, usuario_id):
        """Obtener historial filtrado por usuario"""
        historial = ItemHistoryService.obtener_historial_completo(item)
        return [
            evento for evento in historial 
            if evento.get('usuario', {}).get('id') == str(usuario_id)
        ]
    
    @staticmethod
    def obtener_historial_por_fecha(item, fecha_desde=None, fecha_hasta=None):
        """Obtener historial filtrado por rango de fechas"""
        historial = ItemHistoryService.obtener_historial_completo(item)
        
        if not fecha_desde and not fecha_hasta:
            return historial
        
        resultado = []
        for evento in historial:
            fecha_evento = datetime.fromisoformat(evento['fecha'].replace('Z', '+00:00'))
            
            if fecha_desde and fecha_evento < fecha_desde:
                continue
            
            if fecha_hasta and fecha_evento > fecha_hasta:
                continue
            
            resultado.append(evento)
        
        return resultado
    
    @staticmethod
    def generar_reporte_trazabilidad(item):
        """Generar reporte completo de trazabilidad del ítem"""
        historial = ItemHistoryService.obtener_historial_completo(item)
        
        # Estadísticas del historial
        tipos_eventos = {}
        usuarios_involucrados = set()
        ubicaciones_visitadas = set()
        
        for evento in historial:
            # Contar tipos de eventos
            tipo = evento.get('tipo', 'desconocido')
            tipos_eventos[tipo] = tipos_eventos.get(tipo, 0) + 1
            
            # Usuarios involucrados
            if evento.get('usuario', {}).get('username'):
                usuarios_involucrados.add(evento['usuario']['username'])
            
            # Ubicaciones visitadas
            if evento.get('ubicacion_origen'):
                ubicacion = evento['ubicacion_origen']
                if ubicacion.get('hidrologica') and ubicacion.get('acueducto'):
                    ubicaciones_visitadas.add(
                        f"{ubicacion['hidrologica']['nombre']} - {ubicacion['acueducto']['nombre']}"
                    )
            
            if evento.get('ubicacion_destino'):
                ubicacion = evento['ubicacion_destino']
                if ubicacion.get('hidrologica') and ubicacion.get('acueducto'):
                    ubicaciones_visitadas.add(
                        f"{ubicacion['hidrologica']['nombre']} - {ubicacion['acueducto']['nombre']}"
                    )
        
        return {
            'item': {
                'id': str(item.id),
                'sku': item.sku,
                'nombre': item.nombre,
                'tipo': item.tipo,
                'estado_actual': item.estado,
                'ubicacion_actual': item.ubicacion_actual
            },
            'estadisticas': {
                'total_eventos': len(historial),
                'tipos_eventos': tipos_eventos,
                'usuarios_involucrados': list(usuarios_involucrados),
                'ubicaciones_visitadas': list(ubicaciones_visitadas),
                'fecha_primer_evento': historial[-1]['fecha'] if historial else None,
                'fecha_ultimo_evento': historial[0]['fecha'] if historial else None
            },
            'historial_completo': historial
        }


class InventoryService:
    """
    Servicio principal para operaciones de inventario
    """
    
    @staticmethod
    @transaction.atomic
    def crear_item(datos_item, usuario=None):
        """
        Crear un nuevo ítem de inventario con historial inicial
        
        Args:
            datos_item: Diccionario con datos del ítem
            usuario: Usuario que crea el ítem
        
        Returns:
            ItemInventario: El ítem creado
        """
        # Crear el ítem
        item = ItemInventario.objects.create(**datos_item)
        
        # Registrar evento de creación
        ItemHistoryService.registrar_creacion(
            item=item,
            usuario=usuario,
            observaciones=f"Ítem creado por {usuario.username if usuario else 'sistema'}"
        )
        
        return item
    
    @staticmethod
    @transaction.atomic
    def actualizar_item(item, datos_actualizacion, usuario=None):
        """
        Actualizar un ítem y registrar los cambios en el historial
        
        Args:
            item: ItemInventario instance
            datos_actualizacion: Diccionario con campos a actualizar
            usuario: Usuario que realiza la actualización
        
        Returns:
            ItemInventario: El ítem actualizado
        """
        campos_modificados = []
        
        # Actualizar campos y registrar cambios
        for campo, valor in datos_actualizacion.items():
            if hasattr(item, campo) and getattr(item, campo) != valor:
                setattr(item, campo, valor)
                campos_modificados.append(campo)
        
        if campos_modificados:
            item.save()
            
            # Registrar evento de actualización
            ItemHistoryService.registrar_actualizacion(
                item=item,
                campos_modificados=campos_modificados,
                usuario=usuario,
                observaciones=f"Campos actualizados: {', '.join(campos_modificados)}"
            )
        
        return item
    
    @staticmethod
    @transaction.atomic
    def cambiar_estado_item(item, nuevo_estado, usuario=None, motivo="", observaciones=""):
        """
        Cambiar estado de un ítem y registrar en historial
        
        Args:
            item: ItemInventario instance
            nuevo_estado: Nuevo estado del ítem
            usuario: Usuario que realiza el cambio
            motivo: Motivo del cambio de estado
            observaciones: Observaciones adicionales
        
        Returns:
            ItemInventario: El ítem con estado actualizado
        """
        estado_anterior = item.estado
        
        if estado_anterior != nuevo_estado:
            item.estado = nuevo_estado
            item.save(update_fields=['estado', 'updated_at'])
            
            # Registrar evento de cambio de estado
            ItemHistoryService.registrar_cambio_estado(
                item=item,
                estado_anterior=estado_anterior,
                nuevo_estado=nuevo_estado,
                usuario=usuario,
                motivo=motivo,
                observaciones=observaciones
            )
        
        return item
    
    @staticmethod
    def buscar_items_por_criterios(hidrologica_id=None, tipo=None, estado=None, 
                                 acueducto_id=None, search_term=None):
        """
        Buscar ítems por diferentes criterios
        
        Args:
            hidrologica_id: ID de la hidrológica
            tipo: Tipo de ítem
            estado: Estado del ítem
            acueducto_id: ID del acueducto
            search_term: Término de búsqueda (SKU, nombre, descripción)
        
        Returns:
            QuerySet: Ítems que coinciden con los criterios
        """
        queryset = ItemInventario.objects.all()
        
        if hidrologica_id:
            queryset = queryset.filter(hidrologica_id=hidrologica_id)
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if acueducto_id:
            queryset = queryset.filter(acueducto_actual_id=acueducto_id)
        
        if search_term:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(sku__icontains=search_term) |
                Q(nombre__icontains=search_term) |
                Q(descripcion__icontains=search_term)
            )
        
        return queryset.order_by('-updated_at')
    
    @staticmethod
    def obtener_estadisticas_inventario(hidrologica_id=None):
        """
        Obtener estadísticas del inventario
        
        Args:
            hidrologica_id: ID de la hidrológica (opcional)
        
        Returns:
            dict: Estadísticas del inventario
        """
        from django.db.models import Count
        
        queryset = ItemInventario.objects.all()
        if hidrologica_id:
            queryset = queryset.filter(hidrologica_id=hidrologica_id)
        
        # Estadísticas por tipo
        por_tipo = queryset.values('tipo').annotate(
            total=Count('id')
        ).order_by('tipo')
        
        # Estadísticas por estado
        por_estado = queryset.values('estado').annotate(
            total=Count('id')
        ).order_by('estado')
        
        # Estadísticas por acueducto
        por_acueducto = queryset.values(
            'acueducto_actual__nombre',
            'acueducto_actual__hidrologica__nombre'
        ).annotate(
            total=Count('id')
        ).order_by('acueducto_actual__hidrologica__nombre', 'acueducto_actual__nombre')
        
        return {
            'total_items': queryset.count(),
            'por_tipo': list(por_tipo),
            'por_estado': list(por_estado),
            'por_acueducto': list(por_acueducto)
        }