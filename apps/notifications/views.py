"""
Views para notificaciones
"""
from datetime import datetime, timedelta
from django.db.models import Q, Count, Avg
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.core.permissions import IsOwnerOrReadOnly
from .models import Notificacion, CanalNotificacion, PlantillaNotificacion, TipoNotificacion
from .serializers import (
    NotificacionSerializer, NotificacionListSerializer, MarcarLeidaSerializer,
    CanalNotificacionSerializer, PlantillaNotificacionSerializer,
    ContadorNotificacionesSerializer, EstadisticasNotificacionesSerializer
)
from .services import notification_service


class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestión de notificaciones del usuario
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return NotificacionListSerializer
        return NotificacionSerializer
    
    def get_queryset(self):
        """Filtrar notificaciones del usuario actual"""
        queryset = Notificacion.objects.filter(usuario=self.request.user)
        
        # Filtros opcionales
        solo_no_leidas = self.request.query_params.get('solo_no_leidas', 'false').lower() == 'true'
        tipo = self.request.query_params.get('tipo')
        prioridad = self.request.query_params.get('prioridad')
        
        if solo_no_leidas:
            queryset = queryset.filter(leida=False)
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        if prioridad:
            queryset = queryset.filter(prioridad=prioridad)
        
        # Excluir notificaciones expiradas
        queryset = queryset.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def marcar_leidas(self, request):
        """
        Marcar notificaciones como leídas
        """
        serializer = MarcarLeidaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        notificacion_ids = serializer.validated_data.get('notificacion_ids')
        
        if notificacion_ids:
            # Marcar notificaciones específicas
            count = 0
            for notif_id in notificacion_ids:
                if notification_service.marcar_como_leida(notif_id, request.user.id):
                    count += 1
            
            return Response({
                'message': f'{count} notificaciones marcadas como leídas',
                'marcadas': count
            })
        else:
            # Marcar todas como leídas
            count = notification_service.marcar_todas_como_leidas(request.user.id)
            
            return Response({
                'message': f'Todas las notificaciones marcadas como leídas',
                'marcadas': count
            })
    
    @action(detail=True, methods=['post'])
    def marcar_leida(self, request, pk=None):
        """
        Marcar una notificación específica como leída
        """
        success = notification_service.marcar_como_leida(pk, request.user.id)
        
        if success:
            return Response({'message': 'Notificación marcada como leída'})
        else:
            return Response(
                {'error': 'Notificación no encontrada o ya estaba leída'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def contador(self, request):
        """
        Obtener contador de notificaciones
        """
        usuario = request.user
        
        # Contador de no leídas
        no_leidas = notification_service.obtener_contador_no_leidas(usuario.id)
        
        # Total de notificaciones activas
        total = Notificacion.objects.filter(
            usuario=usuario
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).count()
        
        # Por tipo
        por_tipo = {}
        tipos_count = Notificacion.objects.filter(
            usuario=usuario,
            leida=False
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).values('tipo').annotate(count=Count('id'))
        
        for item in tipos_count:
            tipo_display = dict(TipoNotificacion.choices).get(item['tipo'], item['tipo'])
            por_tipo[tipo_display] = item['count']
        
        # Por prioridad
        por_prioridad = {}
        prioridades_count = Notificacion.objects.filter(
            usuario=usuario,
            leida=False
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).values('prioridad').annotate(count=Count('id'))
        
        for item in prioridades_count:
            por_prioridad[item['prioridad']] = item['count']
        
        data = {
            'total': total,
            'no_leidas': no_leidas,
            'por_tipo': por_tipo,
            'por_prioridad': por_prioridad
        }
        
        serializer = ContadorNotificacionesSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtener estadísticas de notificaciones del usuario
        """
        usuario = request.user
        periodo = request.query_params.get('periodo', '30')  # días
        
        try:
            dias = int(periodo)
        except ValueError:
            dias = 30
        
        fecha_inicio = timezone.now() - timedelta(days=dias)
        
        # Notificaciones en el período
        notificaciones = Notificacion.objects.filter(
            usuario=usuario,
            created_at__gte=fecha_inicio
        )
        
        total_enviadas = notificaciones.count()
        total_leidas = notificaciones.filter(leida=True).count()
        
        porcentaje_lectura = 0
        if total_enviadas > 0:
            porcentaje_lectura = (total_leidas / total_enviadas) * 100
        
        # Por tipo
        por_tipo = {}
        tipos_stats = notificaciones.values('tipo').annotate(
            total=Count('id'),
            leidas=Count('id', filter=Q(leida=True))
        )
        
        for item in tipos_stats:
            tipo_display = dict(TipoNotificacion.choices).get(item['tipo'], item['tipo'])
            por_tipo[tipo_display] = {
                'total': item['total'],
                'leidas': item['leidas'],
                'porcentaje': (item['leidas'] / item['total'] * 100) if item['total'] > 0 else 0
            }
        
        # Tiempo promedio de lectura (en horas)
        tiempo_promedio = 0
        notificaciones_leidas = notificaciones.filter(
            leida=True,
            fecha_lectura__isnull=False
        )
        
        if notificaciones_leidas.exists():
            # Calcular diferencia promedio entre created_at y fecha_lectura
            tiempos = []
            for notif in notificaciones_leidas:
                diff = notif.fecha_lectura - notif.created_at
                tiempos.append(diff.total_seconds() / 3600)  # Convertir a horas
            
            if tiempos:
                tiempo_promedio = sum(tiempos) / len(tiempos)
        
        data = {
            'periodo': f'{dias} días',
            'total_enviadas': total_enviadas,
            'total_leidas': total_leidas,
            'porcentaje_lectura': round(porcentaje_lectura, 2),
            'por_tipo': por_tipo,
            'tiempo_promedio_lectura': round(tiempo_promedio, 2)
        }
        
        serializer = EstadisticasNotificacionesSerializer(data)
        return Response(serializer.data)


class CanalNotificacionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para configuración de canal de notificaciones
    """
    serializer_class = CanalNotificacionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Solo el canal del usuario actual"""
        return CanalNotificacion.objects.filter(usuario=self.request.user)
    
    def get_object(self):
        """Obtener o crear el canal del usuario"""
        canal, created = CanalNotificacion.objects.get_or_create(
            usuario=self.request.user,
            defaults={
                'tipos_habilitados': [choice[0] for choice in TipoNotificacion.choices]
            }
        )
        return canal
    
    def list(self, request, *args, **kwargs):
        """Retornar la configuración del usuario"""
        canal = self.get_object()
        serializer = self.get_serializer(canal)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Actualizar configuración del canal"""
        canal = self.get_object()
        serializer = self.get_serializer(canal, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Configuración de notificaciones actualizada',
            'data': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def test_configuracion(self, request):
        """
        Probar configuración de notificaciones
        """
        canal = self.get_object()
        
        # Verificar si puede recibir notificaciones ahora
        puede_recibir = canal.puede_recibir_notificacion()
        
        # Enviar notificación de prueba si está habilitado
        if puede_recibir:
            notification_service.enviar_notificacion(
                usuario_id=request.user.id,
                tipo=TipoNotificacion.SISTEMA,
                titulo="Prueba de configuración",
                mensaje="Esta es una notificación de prueba para verificar tu configuración.",
                expires_hours=1
            )
            
            return Response({
                'message': 'Notificación de prueba enviada exitosamente',
                'puede_recibir': True
            })
        else:
            return Response({
                'message': 'No se puede enviar notificación según tu configuración actual',
                'puede_recibir': False,
                'razon': 'Fuera del horario o día configurado'
            })


class PlantillaNotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar plantillas de notificación (solo lectura)
    """
    queryset = PlantillaNotificacion.objects.filter(activa=True)
    serializer_class = PlantillaNotificacionSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """
        Vista previa de plantilla con variables de ejemplo
        """
        plantilla = self.get_object()
        variables = request.data.get('variables', {})
        
        try:
            titulo, mensaje = plantilla.generar_contenido(**variables)
            
            return Response({
                'titulo': titulo,
                'mensaje': mensaje,
                'variables_usadas': variables
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )