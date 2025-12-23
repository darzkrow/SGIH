"""
Vistas para transferencias
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.core.exceptions import ValidationError
from django.http import HttpResponse, Http404
from .models import TransferenciaExterna, MovimientoInterno, EstadoTransferencia
from .serializers import (
    TransferenciaExternaListSerializer, TransferenciaExternaDetailSerializer,
    TransferenciaExternaCreateSerializer, MovimientoInternoSerializer,
    AprobacionTransferenciaSerializer, BusquedaStockSerializer,
    ConfirmacionQRSerializer
)
from .services import TransferService, MovimientoInternoService
from .qr_service import QRService
from apps.core.permissions import (
    TransferPermissions, IsEnteRector, CanApproveTransfers, CanValidateQR
)


class TransferenciaExternaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de transferencias externas
    """
    queryset = TransferenciaExterna.objects.all()
    permission_classes = [TransferPermissions]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'prioridad', 'hidrologica_origen', 'hidrologica_destino']
    search_fields = ['numero_orden', 'motivo', 'observaciones']
    ordering_fields = ['fecha_solicitud', 'fecha_aprobacion', 'prioridad']
    ordering = ['-fecha_solicitud']
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción"""
        if self.action == 'list':
            return TransferenciaExternaListSerializer
        elif self.action == 'create':
            return TransferenciaExternaCreateSerializer
        else:
            return TransferenciaExternaDetailSerializer
    
    def get_queryset(self):
        """
        Filtrar transferencias según el usuario
        El filtrado automático se maneja en los managers
        """
        return TransferenciaExterna.objects.select_related(
            'hidrologica_origen', 'hidrologica_destino',
            'acueducto_origen', 'acueducto_destino',
            'solicitado_por', 'aprobado_por'
        ).prefetch_related('items_transferencia__item')
    
    @action(detail=True, methods=['post'], permission_classes=[CanApproveTransfers])
    def aprobar_rechazar(self, request, pk=None):
        """
        Aprobar o rechazar una transferencia (solo Ente Rector)
        """
        transferencia = self.get_object()
        serializer = AprobacionTransferenciaSerializer(data=request.data)
        
        if serializer.is_valid():
            accion = serializer.validated_data['accion']
            observaciones = serializer.validated_data.get('observaciones', '')
            
            try:
                if accion == 'aprobar':
                    transferencia_actualizada = TransferService.aprobar_transferencia(
                        transferencia.id, request.user, observaciones
                    )
                    return Response({
                        'success': True,
                        'message': 'Transferencia aprobada exitosamente',
                        'estado': transferencia_actualizada.estado,
                        'fecha_aprobacion': transferencia_actualizada.fecha_aprobacion
                    })
                
                elif accion == 'rechazar':
                    motivo_rechazo = serializer.validated_data['motivo_rechazo']
                    transferencia_actualizada = TransferService.rechazar_transferencia(
                        transferencia.id, request.user, motivo_rechazo
                    )
                    return Response({
                        'success': True,
                        'message': 'Transferencia rechazada',
                        'estado': transferencia_actualizada.estado,
                        'motivo_rechazo': motivo_rechazo
                    })
                
            except ValidationError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def iniciar_transito(self, request, pk=None):
        """
        Iniciar tránsito de la transferencia (confirmar salida)
        """
        transferencia = self.get_object()
        
        try:
            transferencia_actualizada = TransferService.iniciar_transito(
                transferencia.id, request.user
            )
            return Response({
                'success': True,
                'message': 'Tránsito iniciado exitosamente',
                'estado': transferencia_actualizada.estado,
                'fecha_inicio_transito': transferencia_actualizada.fecha_inicio_transito,
                'firma_origen': transferencia_actualizada.firma_origen
            })
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def completar(self, request, pk=None):
        """
        Completar transferencia (confirmar recepción)
        """
        transferencia = self.get_object()
        
        try:
            transferencia_actualizada = TransferService.completar_transferencia(
                transferencia.id, request.user
            )
            return Response({
                'success': True,
                'message': 'Transferencia completada exitosamente',
                'estado': transferencia_actualizada.estado,
                'fecha_completada': transferencia_actualizada.fecha_completada,
                'firma_destino': transferencia_actualizada.firma_destino
            })
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def descargar_pdf(self, request, pk=None):
        """
        Descargar PDF de la orden de traspaso
        """
        transferencia = self.get_object()
        
        if not transferencia.pdf_generado or not transferencia.archivo_pdf:
            return Response(
                {'error': 'PDF no disponible'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            from django.core.files.storage import default_storage
            
            if default_storage.exists(transferencia.archivo_pdf.name):
                with default_storage.open(transferencia.archivo_pdf.name, 'rb') as pdf_file:
                    response = HttpResponse(
                        pdf_file.read(),
                        content_type='application/pdf'
                    )
                    response['Content-Disposition'] = f'attachment; filename="orden_{transferencia.numero_orden}.pdf"'
                    return response
            else:
                return Response(
                    {'error': 'Archivo PDF no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            return Response(
                {'error': f'Error al descargar PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], permission_classes=[CanApproveTransfers])
    def pendientes_aprobacion(self, request):
        """
        Obtener transferencias pendientes de aprobación (solo Ente Rector)
        """
        transferencias = TransferService.obtener_transferencias_pendientes()
        serializer = TransferenciaExternaListSerializer(
            transferencias,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsEnteRector])
    def buscar_stock_disponible(self, request):
        """
        Buscar stock disponible por tipo (solo Ente Rector)
        """
        serializer = BusquedaStockSerializer(data=request.data)
        
        if serializer.is_valid():
            tipo_item = serializer.validated_data['tipo_item']
            hidrologica_excluir = serializer.validated_data.get('hidrologica_excluir')
            
            stock = TransferService.buscar_stock_disponible(
                tipo_item, hidrologica_excluir
            )
            
            return Response({
                'tipo_item': tipo_item,
                'stock_por_hidrologica': stock,
                'total_hidrologicas': len(stock)
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MovimientoInternoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consulta de movimientos internos
    """
    queryset = MovimientoInterno.objects.all()
    serializer_class = MovimientoInternoSerializer
    permission_classes = [TransferPermissions]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['acueducto_origen', 'acueducto_destino', 'usuario']
    search_fields = ['item__sku', 'item__nombre', 'motivo']
    ordering_fields = ['fecha_movimiento']
    ordering = ['-fecha_movimiento']
    
    def get_queryset(self):
        """Filtrar movimientos por hidrológica del usuario"""
        user = self.request.user
        
        if user.is_ente_rector:
            return MovimientoInterno.objects.select_related(
                'item', 'acueducto_origen', 'acueducto_destino', 'usuario'
            )
        elif user.hidrologica:
            return MovimientoInterno.objects.filter(
                acueducto_origen__hidrologica=user.hidrologica
            ).select_related(
                'item', 'acueducto_origen', 'acueducto_destino', 'usuario'
            )
        else:
            return MovimientoInterno.objects.none()
    
    @action(detail=False, methods=['get'])
    def por_item(self, request):
        """
        Obtener movimientos de un ítem específico
        """
        item_id = request.query_params.get('item_id')
        if not item_id:
            return Response(
                {'error': 'Se requiere item_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            historial = MovimientoInternoService.obtener_historial_item(item_id)
            return Response(historial)
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class QRValidationViewSet(viewsets.ViewSet):
    """
    ViewSet para validación de códigos QR (acceso público)
    """
    permission_classes = [CanValidateQR]
    
    @action(detail=False, methods=['get'])
    def validar(self, request):
        """
        Validar token QR y mostrar información de transferencia
        """
        token = request.query_params.get('token')
        signature = request.query_params.get('sig')
        timestamp = request.query_params.get('ts')
        transferencia_id = request.query_params.get('id')
        
        if not token:
            return Response(
                {'error': 'Token requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar QR
        resultado = QRService.validar_qr_token(
            token, signature, timestamp, transferencia_id
        )
        
        return Response(resultado)
    
    @action(detail=False, methods=['post'])
    def confirmar_accion(self, request):
        """
        Confirmar acción via QR (iniciar tránsito o completar)
        Requiere autenticación
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Autenticación requerida'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = ConfirmacionQRSerializer(data=request.data)
        
        if serializer.is_valid():
            token = serializer.validated_data['token']
            accion = serializer.validated_data['accion']
            observaciones = serializer.validated_data.get('observaciones', '')
            
            resultado = QRService.confirmar_accion_qr(
                token, accion, request.user, observaciones
            )
            
            if resultado['valido']:
                return Response(resultado)
            else:
                return Response(
                    resultado,
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def generar_qr(self, request):
        """
        Generar código QR para una transferencia (solo para testing)
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Autenticación requerida'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        transferencia_id = request.query_params.get('transferencia_id')
        if not transferencia_id:
            return Response(
                {'error': 'transferencia_id requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            qr_info = QRService.generar_qr_para_transferencia(transferencia_id)
            
            # Retornar información del QR (sin la imagen por ahora)
            return Response({
                'token': qr_info['token'],
                'url_firmada': qr_info['url_firmada'],
                'transferencia_id': qr_info['transferencia_id'],
                'numero_orden': qr_info['numero_orden']
            })
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )