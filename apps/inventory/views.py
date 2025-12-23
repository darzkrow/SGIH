"""
Vistas para inventario con filtrado multitenente
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Sum
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import ItemInventario, CategoriaItem, TipoItem, EstadoItem
from .serializers import (
    ItemInventarioListSerializer, ItemInventarioDetailSerializer,
    ItemInventarioCreateSerializer, CategoriaItemSerializer,
    MovimientoInternoSerializer, BusquedaGlobalSerializer,
    EstadisticasInventarioSerializer
)
from .services import InventoryService, ItemHistoryService
from apps.core.permissions import (
    InventoryPermissions, IsEnteRector, MultiTenantPermission
)
from apps.transfers.services import MovimientoInternoService


@extend_schema_view(
    list=extend_schema(
        summary="Listar ítems de inventario",
        description="Obtiene la lista de ítems de inventario filtrada por la hidrológica del usuario. "
                   "Soporta filtrado por tipo, estado, categoría y búsqueda por texto.",
        parameters=[
            OpenApiParameter(
                name='tipo',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filtrar por tipo de ítem',
                enum=[choice[0] for choice in TipoItem.choices]
            ),
            OpenApiParameter(
                name='estado',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filtrar por estado del ítem',
                enum=[choice[0] for choice in EstadoItem.choices]
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Buscar por SKU, nombre, descripción o proveedor'
            ),
        ]
    ),
    create=extend_schema(
        summary="Crear ítem de inventario",
        description="Crea un nuevo ítem de inventario en la hidrológica del usuario."
    ),
    retrieve=extend_schema(
        summary="Obtener ítem de inventario",
        description="Obtiene los detalles completos de un ítem de inventario específico."
    ),
    update=extend_schema(
        summary="Actualizar ítem de inventario",
        description="Actualiza completamente un ítem de inventario."
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente ítem de inventario",
        description="Actualiza parcialmente un ítem de inventario."
    ),
    destroy=extend_schema(
        summary="Eliminar ítem de inventario",
        description="Elimina un ítem de inventario (solo si no tiene movimientos asociados)."
    )
)
class ItemInventarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de ítems de inventario con multitenencia
    
    Proporciona operaciones CRUD completas para ítems de inventario con:
    - Filtrado automático por hidrológica del usuario
    - Búsqueda por múltiples campos
    - Filtrado por tipo, estado y categoría
    - Acciones especiales para movimientos y estadísticas
    """
    queryset = ItemInventario.objects.all()
    permission_classes = [InventoryPermissions]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tipo', 'estado', 'categoria', 'acueducto_actual']
    search_fields = ['sku', 'nombre', 'descripcion', 'proveedor']
    ordering_fields = ['created_at', 'nombre', 'sku', 'valor_unitario']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción"""
        if self.action == 'list':
            return ItemInventarioListSerializer
        elif self.action == 'create':
            return ItemInventarioCreateSerializer
        else:
            return ItemInventarioDetailSerializer
    
    def get_queryset(self):
        """
        Filtrar queryset según el usuario y rol
        El filtrado automático por tenant se maneja en los managers
        """
        queryset = ItemInventario.objects.select_related(
            'hidrologica', 'acueducto_actual', 'categoria'
        )
        
        # Los managers ya aplican el filtrado por tenant automáticamente
        return queryset
    
    def perform_create(self, serializer):
        """Crear ítem asegurando multitenencia"""
        user = self.request.user
        
        # Si no es Ente Rector, forzar la hidrológica del usuario
        if not user.is_ente_rector and user.hidrologica:
            serializer.save(hidrologica=user.hidrologica)
        else:
            serializer.save()
    
    @extend_schema(
        summary="Realizar movimiento interno",
        description="Mueve un ítem de inventario a otro acueducto dentro de la misma hidrológica.",
        request=MovimientoInternoSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'movimiento_id': {'type': 'string'},
                    'nueva_ubicacion': {'type': 'string'}
                }
            }
        }
    )
    @action(detail=True, methods=['post'])
    def mover_interno(self, request, pk=None):
        """
        Realizar movimiento interno del ítem
        """
        item = self.get_object()
        serializer = MovimientoInternoSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                movimiento = MovimientoInternoService.crear_movimiento_interno(
                    item_id=item.id,
                    acueducto_destino_id=serializer.validated_data['acueducto_destino_id'],
                    usuario=request.user,
                    motivo=serializer.validated_data['motivo'],
                    observaciones=serializer.validated_data.get('observaciones', '')
                )
                
                return Response({
                    'success': True,
                    'message': 'Movimiento interno realizado exitosamente',
                    'movimiento_id': str(movimiento.id),
                    'nueva_ubicacion': item.ubicacion_actual
                })
                
            except ValidationError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Cambiar estado del ítem",
        description="Cambia el estado de un ítem de inventario y registra el cambio en el historial.",
        request={
            'type': 'object',
            'properties': {
                'estado': {
                    'type': 'string',
                    'enum': [choice[0] for choice in EstadoItem.choices],
                    'description': 'Nuevo estado del ítem'
                },
                'observaciones': {
                    'type': 'string',
                    'description': 'Observaciones sobre el cambio de estado'
                }
            },
            'required': ['estado']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'estado_anterior': {'type': 'string'},
                    'estado_nuevo': {'type': 'string'}
                }
            }
        }
    )
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """
        Cambiar estado del ítem
        """
        item = self.get_object()
        nuevo_estado = request.data.get('estado')
        observaciones = request.data.get('observaciones', '')
        
        if not nuevo_estado:
            return Response(
                {'error': 'Se requiere el campo estado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if nuevo_estado not in [choice[0] for choice in EstadoItem.choices]:
            return Response(
                {'error': 'Estado no válido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item.cambiar_estado(nuevo_estado, request.user, observaciones)
            
            return Response({
                'success': True,
                'message': 'Estado cambiado exitosamente',
                'estado_anterior': item.estado,
                'estado_nuevo': nuevo_estado
            })
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        summary="Obtener historial completo del ítem",
        description="Obtiene el historial completo de movimientos y cambios de estado de un ítem.",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'historial': {
                        'type': 'array',
                        'items': {'type': 'object'}
                    }
                }
            }
        }
    )
    @action(detail=True, methods=['get'])
    def historial_completo(self, request, pk=None):
        """
        Obtener historial completo del ítem
        """
        item = self.get_object()
        
        try:
            historial = MovimientoInternoService.obtener_historial_item(item.id)
            return Response(historial)
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        summary="Búsqueda global de inventario",
        description="Búsqueda global para Ente Rector con vista anonimizada de todos los inventarios.",
        request=BusquedaGlobalSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'total_encontrados': {'type': 'integer'},
                    'items': {
                        'type': 'array',
                        'items': {'$ref': '#/components/schemas/ItemInventarioList'}
                    },
                    'query': {'type': 'string'}
                }
            }
        }
    )
    @action(detail=False, methods=['post'])
    def busqueda_global(self, request):
        """
        Búsqueda global para Ente Rector (vista anonimizada)
        """
        if not request.user.is_ente_rector:
            return Response(
                {'error': 'Solo el Ente Rector puede realizar búsquedas globales'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BusquedaGlobalSerializer(data=request.data)
        if serializer.is_valid():
            query = serializer.validated_data['query']
            tipo = serializer.validated_data.get('tipo')
            estado = serializer.validated_data.get('estado')
            hidrologica_id = serializer.validated_data.get('hidrologica_id')
            
            # Usar manager para búsqueda global
            queryset = ItemInventario.objects.buscar_global(query)
            
            # Aplicar filtros adicionales
            if tipo:
                queryset = queryset.filter(tipo=tipo)
            if estado:
                queryset = queryset.filter(estado=estado)
            if hidrologica_id:
                queryset = queryset.filter(hidrologica_id=hidrologica_id)
            
            # Serializar con vista anonimizada
            items = ItemInventarioListSerializer(
                queryset[:50],  # Limitar resultados
                many=True,
                context={'request': request}
            ).data
            
            return Response({
                'total_encontrados': queryset.count(),
                'items': items,
                'query': query,
                'vista': 'anonimizada'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtener estadísticas de inventario
        """
        user = request.user
        
        if user.is_ente_rector:
            # Estadísticas globales para Ente Rector
            queryset = ItemInventario.objects.all()
            
            # Estadísticas por hidrológica
            por_hidrologica = {}
            for hidrologica_data in queryset.values('hidrologica__nombre', 'hidrologica__codigo').annotate(
                total=Count('id'),
                valor_total=Sum('valor_unitario')
            ):
                hidrologica_key = hidrologica_data['hidrologica__codigo']
                por_hidrologica[hidrologica_key] = {
                    'nombre': hidrologica_data['hidrologica__nombre'],
                    'total_items': hidrologica_data['total'],
                    'valor_total': float(hidrologica_data['valor_total'] or 0)
                }
            
        else:
            # Estadísticas de la hidrológica del usuario
            queryset = ItemInventario.objects.filter(hidrologica=user.hidrologica)
            por_hidrologica = None
        
        # Estadísticas generales
        total_items = queryset.count()
        valor_total = queryset.aggregate(Sum('valor_unitario'))['valor_unitario__sum'] or 0
        
        # Por tipo
        por_tipo = {}
        for tipo_data in queryset.values('tipo').annotate(total=Count('id')):
            tipo_key = tipo_data['tipo']
            por_tipo[tipo_key] = {
                'total': tipo_data['total'],
                'display': dict(TipoItem.choices)[tipo_key]
            }
        
        # Por estado
        por_estado = {}
        for estado_data in queryset.values('estado').annotate(total=Count('id')):
            estado_key = estado_data['estado']
            por_estado[estado_key] = {
                'total': estado_data['total'],
                'display': dict(EstadoItem.choices)[estado_key]
            }
        
        # Por acueducto (solo para operadores)
        por_acueducto = None
        if not user.is_ente_rector and user.hidrologica:
            por_acueducto = {}
            for acueducto_data in queryset.values(
                'acueducto_actual__nombre', 'acueducto_actual__codigo'
            ).annotate(total=Count('id')):
                acueducto_key = acueducto_data['acueducto_actual__codigo']
                por_acueducto[acueducto_key] = {
                    'nombre': acueducto_data['acueducto_actual__nombre'],
                    'total_items': acueducto_data['total']
                }
        
        estadisticas = {
            'total_items': total_items,
            'por_tipo': por_tipo,
            'por_estado': por_estado,
            'valor_total': valor_total,
            'items_disponibles': queryset.filter(estado=EstadoItem.DISPONIBLE).count(),
            'items_en_transito': queryset.filter(estado=EstadoItem.EN_TRANSITO).count(),
        }
        
        if por_acueducto:
            estadisticas['por_acueducto'] = por_acueducto
        
        if por_hidrologica:
            estadisticas['por_hidrologica'] = por_hidrologica
        
        serializer = EstadisticasInventarioSerializer(estadisticas)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def disponibles_para_transferencia(self, request):
        """
        Obtener ítems disponibles para transferencia
        """
        queryset = self.get_queryset().filter(
            estado__in=[EstadoItem.DISPONIBLE, EstadoItem.ASIGNADO]
        )
        
        # Aplicar filtros de búsqueda si se proporcionan
        tipo = request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(sku__icontains=search) |
                Q(nombre__icontains=search) |
                Q(descripcion__icontains=search)
            )
        
        serializer = ItemInventarioListSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        """
        Obtener historial completo del ítem
        """
        item = self.get_object()
        
        # Parámetros de filtrado
        tipo_evento = request.query_params.get('tipo')
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        usuario_id = request.query_params.get('usuario_id')
        
        # Obtener historial
        if tipo_evento:
            historial = ItemHistoryService.obtener_historial_por_tipo(item, tipo_evento)
        elif usuario_id:
            historial = ItemHistoryService.obtener_historial_por_usuario(item, usuario_id)
        elif fecha_desde or fecha_hasta:
            from datetime import datetime
            fecha_desde_dt = datetime.fromisoformat(fecha_desde) if fecha_desde else None
            fecha_hasta_dt = datetime.fromisoformat(fecha_hasta) if fecha_hasta else None
            historial = ItemHistoryService.obtener_historial_por_fecha(
                item, fecha_desde_dt, fecha_hasta_dt
            )
        else:
            historial = ItemHistoryService.obtener_historial_completo(item)
        
        return Response({
            'item_id': str(item.id),
            'item_sku': item.sku,
            'total_eventos': len(historial),
            'historial': historial
        })
    
    @action(detail=True, methods=['get'])
    def trazabilidad(self, request, pk=None):
        """
        Obtener reporte completo de trazabilidad del ítem
        """
        item = self.get_object()
        reporte = ItemHistoryService.generar_reporte_trazabilidad(item)
        
        return Response(reporte)
    
    @action(detail=True, methods=['post'])
    def registrar_mantenimiento(self, request, pk=None):
        """
        Registrar evento de mantenimiento
        """
        item = self.get_object()
        
        tipo_mantenimiento = request.data.get('tipo_mantenimiento')
        observaciones = request.data.get('observaciones', '')
        fecha_inicio = request.data.get('fecha_inicio')
        fecha_fin = request.data.get('fecha_fin')
        
        if not tipo_mantenimiento:
            return Response(
                {'error': 'El tipo de mantenimiento es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convertir fechas si se proporcionan
        from datetime import datetime
        fecha_inicio_dt = None
        fecha_fin_dt = None
        
        if fecha_inicio:
            try:
                fecha_inicio_dt = datetime.fromisoformat(fecha_inicio)
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha_inicio inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if fecha_fin:
            try:
                fecha_fin_dt = datetime.fromisoformat(fecha_fin)
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha_fin inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Registrar evento de mantenimiento
        evento = ItemHistoryService.registrar_mantenimiento(
            item=item,
            tipo_mantenimiento=tipo_mantenimiento,
            usuario=request.user,
            fecha_inicio=fecha_inicio_dt,
            fecha_fin=fecha_fin_dt,
            observaciones=observaciones
        )
        
        return Response({
            'success': True,
            'message': 'Evento de mantenimiento registrado exitosamente',
            'evento_id': evento['id'],
            'evento': evento
        })
    
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """
        Cambiar estado del ítem con registro en historial
        """
        item = self.get_object()
        
        nuevo_estado = request.data.get('estado')
        motivo = request.data.get('motivo', '')
        observaciones = request.data.get('observaciones', '')
        
        if not nuevo_estado:
            return Response(
                {'error': 'El nuevo estado es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if nuevo_estado not in [choice[0] for choice in EstadoItem.choices]:
            return Response(
                {'error': 'Estado inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if item.estado == nuevo_estado:
            return Response(
                {'error': 'El ítem ya está en ese estado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cambiar estado usando el servicio
        InventoryService.cambiar_estado_item(
            item=item,
            nuevo_estado=nuevo_estado,
            usuario=request.user,
            motivo=motivo,
            observaciones=observaciones
        )
        
        return Response({
            'success': True,
            'message': f'Estado cambiado a {nuevo_estado} exitosamente',
            'estado_anterior': item.estado,
            'estado_nuevo': nuevo_estado,
            'ubicacion_actual': item.ubicacion_actual
        })


class CategoriaItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de categorías de ítems
    """
    queryset = CategoriaItem.objects.filter(activa=True)
    serializer_class = CategoriaItemSerializer
    permission_classes = [MultiTenantPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['tipo_item', 'activa']
    search_fields = ['nombre', 'descripcion']
    ordering = ['tipo_item', 'nombre']
    
    def get_permissions(self):
        """Solo Ente Rector puede crear/modificar categorías"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsEnteRector]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]