"""
Tests unitarios para servicios del módulo notifications
"""
import pytest
from unittest.mock import patch, Mock
from django.core.cache import cache

from apps.notifications.services import NotificationService
from apps.notifications.models import (
    Notificacion, CanalNotificacion, PlantillaNotificacion
)


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.services
class TestNotificationService:
    """Tests para NotificationService"""
    
    def setup_method(self):
        """Limpiar cache antes de cada test"""
        cache.clear()
    
    def test_crear_notificacion_simple(self, operador_atlantico_user):
        """Test crear notificación simple"""
        notificacion = NotificationService.crear_notificacion(
            usuario=operador_atlantico_user,
            tipo="nueva_solicitud",
            titulo="Test Notification",
            mensaje="Test message",
            prioridad="alta"
        )
        
        assert notificacion.usuario == operador_atlantico_user
        assert notificacion.tipo == "nueva_solicitud"
        assert notificacion.titulo == "Test Notification"
        assert notificacion.mensaje == "Test message"
        assert notificacion.prioridad == "alta"
        assert notificacion.leida is False
    
    def test_crear_notificacion_con_plantilla(self, operador_atlantico_user):
        """Test crear notificación usando plantilla"""
        # Crear plantilla
        plantilla = PlantillaNotificacion.objects.create(
            tipo="nueva_solicitud",
            titulo_template="Nueva Solicitud #{numero_orden}",
            mensaje_template="Solicitud {numero_orden} de {hidrologica_origen}",
            prioridad_default="alta"
        )
        
        # Crear notificación con plantilla
        notificacion = NotificationService.crear_notificacion_con_plantilla(
            usuario=operador_atlantico_user,
            tipo="nueva_solicitud",
            variables={
                "numero_orden": "SOL-2024-001",
                "hidrologica_origen": "HAT"
            }
        )
        
        assert notificacion.titulo == "Nueva Solicitud #SOL-2024-001"
        assert notificacion.mensaje == "Solicitud SOL-2024-001 de HAT"
        assert notificacion.prioridad == "alta"
    
    def test_crear_notificacion_plantilla_no_existe(self, operador_atlantico_user):
        """Test crear notificación cuando plantilla no existe"""
        with pytest.raises(ValueError, match="Plantilla de notificación no encontrada"):
            NotificationService.crear_notificacion_con_plantilla(
                usuario=operador_atlantico_user,
                tipo="tipo_inexistente",
                variables={}
            )
    
    def test_enviar_notificacion_multiple_usuarios(self, operador_atlantico_user, operador_bolivar_user):
        """Test enviar notificación a múltiples usuarios"""
        usuarios = [operador_atlantico_user, operador_bolivar_user]
        
        notificaciones = NotificationService.enviar_notificacion_multiple(
            usuarios=usuarios,
            tipo="nueva_solicitud",
            titulo="Test Multiple",
            mensaje="Test message",
            prioridad="media"
        )
        
        assert len(notificaciones) == 2
        assert notificaciones[0].usuario == operador_atlantico_user
        assert notificaciones[1].usuario == operador_bolivar_user
        
        for notificacion in notificaciones:
            assert notificacion.titulo == "Test Multiple"
            assert notificacion.mensaje == "Test message"
    
    def test_enviar_notificacion_por_rol(self, operador_atlantico_user, operador_bolivar_user, admin_rector_user):
        """Test enviar notificación por rol"""
        notificaciones = NotificationService.enviar_notificacion_por_rol(
            rol="operador_hidrologica",
            tipo="nueva_solicitud",
            titulo="Test Role",
            mensaje="Test message"
        )
        
        # Debe enviar a ambos operadores
        assert len(notificaciones) == 2
        usuarios_notificados = [n.usuario for n in notificaciones]
        assert operador_atlantico_user in usuarios_notificados
        assert operador_bolivar_user in usuarios_notificados
        assert admin_rector_user not in usuarios_notificados
    
    def test_enviar_notificacion_por_hidrologica(self, operador_atlantico_user, operador_bolivar_user,
                                               hidrologica_atlantico):
        """Test enviar notificación por hidrológica"""
        notificaciones = NotificationService.enviar_notificacion_por_hidrologica(
            hidrologica=hidrologica_atlantico,
            tipo="nueva_solicitud",
            titulo="Test Hidrologica",
            mensaje="Test message"
        )
        
        # Solo debe enviar a usuarios de la hidrológica del Atlántico
        assert len(notificaciones) == 1
        assert notificaciones[0].usuario == operador_atlantico_user
    
    def test_marcar_notificacion_leida(self, operador_atlantico_user):
        """Test marcar notificación como leída"""
        notificacion = NotificationService.crear_notificacion(
            usuario=operador_atlantico_user,
            tipo="nueva_solicitud",
            titulo="Test",
            mensaje="Test"
        )
        
        assert notificacion.leida is False
        
        resultado = NotificationService.marcar_notificacion_leida(
            notificacion_id=notificacion.id,
            usuario=operador_atlantico_user
        )
        
        assert resultado is True
        notificacion.refresh_from_db()
        assert notificacion.leida is True
        assert notificacion.fecha_lectura is not None
    
    def test_marcar_notificacion_leida_usuario_incorrecto(self, operador_atlantico_user, operador_bolivar_user):
        """Test que no permita marcar notificación de otro usuario"""
        notificacion = NotificationService.crear_notificacion(
            usuario=operador_atlantico_user,
            tipo="nueva_solicitud",
            titulo="Test",
            mensaje="Test"
        )
        
        resultado = NotificationService.marcar_notificacion_leida(
            notificacion_id=notificacion.id,
            usuario=operador_bolivar_user  # Usuario diferente
        )
        
        assert resultado is False
        notificacion.refresh_from_db()
        assert notificacion.leida is False
    
    def test_marcar_todas_leidas(self, operador_atlantico_user):
        """Test marcar todas las notificaciones como leídas"""
        # Crear varias notificaciones
        for i in range(3):
            NotificationService.crear_notificacion(
                usuario=operador_atlantico_user,
                tipo="nueva_solicitud",
                titulo=f"Test {i}",
                mensaje="Test"
            )
        
        # Marcar todas como leídas
        count = NotificationService.marcar_todas_leidas(operador_atlantico_user)
        
        assert count == 3
        
        # Verificar que todas están leídas
        notificaciones = Notificacion.objects.filter(usuario=operador_atlantico_user)
        for notificacion in notificaciones:
            assert notificacion.leida is True
    
    def test_obtener_notificaciones_no_leidas(self, operador_atlantico_user):
        """Test obtener notificaciones no leídas"""
        # Crear notificaciones
        notif1 = NotificationService.crear_notificacion(
            usuario=operador_atlantico_user,
            tipo="nueva_solicitud",
            titulo="Test 1",
            mensaje="Test"
        )
        
        notif2 = NotificationService.crear_notificacion(
            usuario=operador_atlantico_user,
            tipo="nueva_solicitud",
            titulo="Test 2",
            mensaje="Test"
        )
        
        # Marcar una como leída
        notif1.marcar_leida()
        
        # Obtener no leídas
        no_leidas = NotificationService.obtener_notificaciones_no_leidas(operador_atlantico_user)
        
        assert len(no_leidas) == 1
        assert no_leidas[0] == notif2
    
    def test_obtener_estadisticas_usuario(self, operador_atlantico_user):
        """Test obtener estadísticas de notificaciones"""
        # Crear notificaciones de diferentes tipos y prioridades
        NotificationService.crear_notificacion(
            usuario=operador_atlantico_user,
            tipo="nueva_solicitud",
            titulo="Test 1",
            mensaje="Test",
            prioridad="alta"
        )
        
        notif2 = NotificationService.crear_notificacion(
            usuario=operador_atlantico_user,
            tipo="transferencia_aprobada",
            titulo="Test 2",
            mensaje="Test",
            prioridad="media"
        )
        
        # Marcar una como leída
        notif2.marcar_leida()
        
        estadisticas = NotificationService.obtener_estadisticas_usuario(operador_atlantico_user)
        
        assert estadisticas["total"] == 2
        assert estadisticas["no_leidas"] == 1
        assert estadisticas["leidas"] == 1
        assert estadisticas["por_tipo"]["nueva_solicitud"] == 1
        assert estadisticas["por_tipo"]["transferencia_aprobada"] == 1
        assert estadisticas["por_prioridad"]["alta"] == 1
        assert estadisticas["por_prioridad"]["media"] == 1
    
    def test_limpiar_notificaciones_antiguas(self, operador_atlantico_user):
        """Test limpiar notificaciones antiguas"""
        from datetime import timedelta
        from django.utils import timezone
        
        # Crear notificación antigua
        notif_antigua = NotificationService.crear_notificacion(
            usuario=operador_atlantico_user,
            tipo="nueva_solicitud",
            titulo="Antigua",
            mensaje="Test"
        )
        
        # Simular que es antigua
        notif_antigua.created_at = timezone.now() - timedelta(days=35)
        notif_antigua.save()
        
        # Crear notificación reciente
        notif_reciente = NotificationService.crear_notificacion(
            usuario=operador_atlantico_user,
            tipo="nueva_solicitud",
            titulo="Reciente",
            mensaje="Test"
        )
        
        # Limpiar notificaciones antiguas (más de 30 días)
        count = NotificationService.limpiar_notificaciones_antiguas(dias=30)
        
        assert count == 1
        
        # Verificar que solo queda la reciente
        notificaciones = Notificacion.objects.filter(usuario=operador_atlantico_user)
        assert len(notificaciones) == 1
        assert notificaciones[0] == notif_reciente
    
    @patch('apps.notifications.services.cache')
    def test_obtener_notificaciones_tiempo_real(self, mock_cache, operador_atlantico_user):
        """Test obtener notificaciones en tiempo real"""
        # Simular notificaciones en cache
        notificaciones_cache = [
            {
                'id': '123',
                'titulo': 'Test Real Time',
                'mensaje': 'Test message',
                'tipo': 'nueva_solicitud',
                'prioridad': 'alta',
                'timestamp': '2024-01-20T10:00:00Z'
            }
        ]
        
        mock_cache.get.return_value = notificaciones_cache
        
        notificaciones = NotificationService.obtener_notificaciones_tiempo_real(operador_atlantico_user)
        
        assert len(notificaciones) == 1
        assert notificaciones[0]['titulo'] == 'Test Real Time'
        
        # Verificar que se llamó al cache con la clave correcta
        cache_key = f"notifications_realtime_{operador_atlantico_user.id}"
        mock_cache.get.assert_called_once_with(cache_key, [])
    
    @patch('apps.notifications.services.cache')
    def test_publicar_notificacion_tiempo_real(self, mock_cache, operador_atlantico_user):
        """Test publicar notificación en tiempo real"""
        notificacion = NotificationService.crear_notificacion(
            usuario=operador_atlantico_user,
            tipo="nueva_solicitud",
            titulo="Test Real Time",
            mensaje="Test message"
        )
        
        # Simular cache vacío inicialmente
        mock_cache.get.return_value = []
        
        NotificationService.publicar_notificacion_tiempo_real(notificacion)
        
        # Verificar que se llamó al cache
        cache_key = f"notifications_realtime_{operador_atlantico_user.id}"
        mock_cache.get.assert_called_with(cache_key, [])
        mock_cache.set.assert_called_once()
        
        # Verificar argumentos del set
        args, kwargs = mock_cache.set.call_args
        assert args[0] == cache_key
        assert len(args[1]) == 1  # Una notificación en la lista
        assert args[1][0]['titulo'] == "Test Real Time"
    
    def test_configurar_canal_notificacion(self, operador_atlantico_user):
        """Test configurar canal de notificación"""
        configuracion = {
            "mostrar_popup": True,
            "sonido": False,
            "filtros_prioridad": ["alta", "media"]
        }
        
        canal = NotificationService.configurar_canal_notificacion(
            usuario=operador_atlantico_user,
            tipo="sistema",
            configuracion=configuracion,
            activo=True
        )
        
        assert canal.usuario == operador_atlantico_user
        assert canal.tipo == "sistema"
        assert canal.activo is True
        assert canal.configuracion == configuracion
    
    def test_configurar_canal_notificacion_actualizar_existente(self, operador_atlantico_user):
        """Test actualizar canal de notificación existente"""
        # Crear canal inicial
        canal_inicial = CanalNotificacion.objects.create(
            usuario=operador_atlantico_user,
            tipo="sistema",
            configuracion={"mostrar_popup": False}
        )
        
        # Actualizar configuración
        nueva_configuracion = {"mostrar_popup": True, "sonido": True}
        
        canal_actualizado = NotificationService.configurar_canal_notificacion(
            usuario=operador_atlantico_user,
            tipo="sistema",
            configuracion=nueva_configuracion,
            activo=True
        )
        
        # Debe ser el mismo canal, actualizado
        assert canal_actualizado.id == canal_inicial.id
        assert canal_actualizado.configuracion == nueva_configuracion
        assert canal_actualizado.activo is True
    
    def test_obtener_canales_usuario(self, operador_atlantico_user):
        """Test obtener canales de notificación de usuario"""
        # Crear varios canales
        CanalNotificacion.objects.create(
            usuario=operador_atlantico_user,
            tipo="sistema",
            activo=True
        )
        
        CanalNotificacion.objects.create(
            usuario=operador_atlantico_user,
            tipo="email",
            activo=False
        )
        
        # Obtener todos los canales
        canales = NotificationService.obtener_canales_usuario(operador_atlantico_user)
        
        assert len(canales) == 2
        
        # Obtener solo canales activos
        canales_activos = NotificationService.obtener_canales_usuario(
            operador_atlantico_user, 
            solo_activos=True
        )
        
        assert len(canales_activos) == 1
        assert canales_activos[0].tipo == "sistema"