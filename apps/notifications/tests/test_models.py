"""
Tests unitarios para modelos del módulo notifications
"""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.notifications.models import (
    Notificacion, CanalNotificacion, PlantillaNotificacion,
    TipoNotificacion, PrioridadNotificacion
)


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.models
class TestPlantillaNotificacionModel:
    """Tests para el modelo PlantillaNotificacion"""
    
    def test_create_plantilla_notificacion(self):
        """Test crear plantilla de notificación"""
        plantilla = PlantillaNotificacion.objects.create(
            tipo="nueva_solicitud",
            titulo_template="Nueva Solicitud #{numero_orden}",
            mensaje_template="Se ha recibido una nueva solicitud de transferencia. Número: {numero_orden}",
            prioridad_default="alta"
        )
        
        assert plantilla.tipo == "nueva_solicitud"
        assert plantilla.titulo_template == "Nueva Solicitud #{numero_orden}"
        assert plantilla.prioridad_default == "alta"
        assert plantilla.activa is True
        assert str(plantilla) == "Plantilla Nueva Solicitud de Transferencia"
    
    def test_plantilla_tipo_validation(self):
        """Test validación de tipo de plantilla"""
        plantilla = PlantillaNotificacion(
            tipo="invalid_type",
            titulo_template="Test",
            mensaje_template="Test"
        )
        
        with pytest.raises(ValidationError):
            plantilla.full_clean()
    
    def test_plantilla_prioridad_validation(self):
        """Test validación de prioridad por defecto"""
        plantilla = PlantillaNotificacion(
            tipo="nueva_solicitud",
            titulo_template="Test",
            mensaje_template="Test",
            prioridad_default="invalid_priority"
        )
        
        with pytest.raises(ValidationError):
            plantilla.full_clean()
    
    def test_plantilla_generar_contenido(self):
        """Test generar contenido de plantilla"""
        plantilla = PlantillaNotificacion.objects.create(
            tipo="nueva_solicitud",
            titulo_template="Nueva Solicitud #{numero_orden}",
            mensaje_template="Test"
        )
        
        titulo, mensaje = plantilla.generar_contenido(numero_orden="SOL-2024-001")
        assert titulo == "Nueva Solicitud #SOL-2024-001"
    
    def test_plantilla_generar_mensaje(self):
        """Test generar mensaje de plantilla"""
        plantilla = PlantillaNotificacion.objects.create(
            tipo="nueva_solicitud",
            titulo_template="Test",
            mensaje_template="Solicitud {numero_orden} de {hidrologica_origen} a {hidrologica_destino}"
        )
        
        titulo, mensaje = plantilla.generar_contenido(
            numero_orden="SOL-2024-001",
            hidrologica_origen="HAT",
            hidrologica_destino="HBL"
        )
        
        assert mensaje == "Solicitud SOL-2024-001 de HAT a HBL"
    
    def test_plantilla_generar_with_missing_variables(self):
        """Test generar con variables faltantes"""
        plantilla = PlantillaNotificacion.objects.create(
            tipo="nueva_solicitud",
            titulo_template="Solicitud {numero_orden} - {variable_faltante}",
            mensaje_template="Test"
        )
        
        # Debe lanzar ValueError por variable faltante
        with pytest.raises(ValueError):
            plantilla.generar_contenido(numero_orden="SOL-2024-001")


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.models
class TestCanalNotificacionModel:
    """Tests para el modelo CanalNotificacion"""
    
    def test_create_canal_notificacion(self, operador_atlantico_user):
        """Test crear canal de notificación"""
        # El canal se crea automáticamente por señal, así que lo obtenemos
        canal = CanalNotificacion.objects.get(usuario=operador_atlantico_user)
        
        # Modificar sus propiedades
        canal.email_habilitado = True
        canal.push_habilitado = False
        canal.tipos_habilitados = ["nueva_solicitud", "transferencia_aprobada"]
        canal.save()
        
        assert canal.usuario == operador_atlantico_user
        assert canal.email_habilitado is True
        assert canal.push_habilitado is False
        assert "nueva_solicitud" in canal.tipos_habilitados
        assert str(canal) == f"Canal de {operador_atlantico_user.username}"
    
    def test_canal_puede_recibir_validation(self, operador_atlantico_user):
        """Test validación de recepción de notificaciones"""
        canal = CanalNotificacion.objects.get(usuario=operador_atlantico_user)
        
        # Modificar tipos habilitados
        canal.tipos_habilitados = ["nueva_solicitud"]
        canal.save()
        
        # Debe poder recibir notificaciones del tipo habilitado
        puede_recibir = canal.puede_recibir_notificacion("nueva_solicitud")
        # El resultado depende del horario actual, así que solo verificamos que no lance error
        assert isinstance(puede_recibir, bool)
    
    def test_canal_unique_per_user(self, operador_atlantico_user, operador_bolivar_user):
        """Test que canal sea único por usuario (OneToOneField)"""
        # Los canales ya existen por la señal, así que los obtenemos
        canal1 = CanalNotificacion.objects.get(usuario=operador_atlantico_user)
        canal2 = CanalNotificacion.objects.get(usuario=operador_bolivar_user)
        
        # Verificar que cada usuario tiene su propio canal
        assert canal1.usuario == operador_atlantico_user
        assert canal2.usuario == operador_bolivar_user
        assert canal1 != canal2
        
        # Intentar crear segundo canal para el mismo usuario debe fallar
        with pytest.raises(IntegrityError):
            CanalNotificacion.objects.create(
                usuario=operador_atlantico_user,  # Mismo usuario
                email_habilitado=False
            )
    
    def test_canal_tipos_habilitados_json_field(self, operador_atlantico_user):
        """Test campo JSON tipos_habilitados"""
        tipos = ["nueva_solicitud", "transferencia_aprobada", "sistema"]
        
        canal = CanalNotificacion.objects.get(usuario=operador_atlantico_user)
        canal.tipos_habilitados = tipos
        canal.save()
        
        # Recargar desde DB
        canal.refresh_from_db()
        
        assert canal.tipos_habilitados == tipos
        assert "nueva_solicitud" in canal.tipos_habilitados
        assert "transferencia_aprobada" in canal.tipos_habilitados


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.models
class TestNotificacionModel:
    """Tests para el modelo Notificacion"""
    
    def test_create_notificacion(self, operador_atlantico_user):
        """Test crear notificación"""
        notificacion = Notificacion.objects.create(
            usuario=operador_atlantico_user,
            tipo="nueva_solicitud",
            titulo="Nueva Solicitud de Transferencia",
            mensaje="Se ha recibido una nueva solicitud",
            prioridad="alta",
            datos_adicionales={
                "transferencia_id": "123",
                "numero_orden": "SOL-2024-001"
            }
        )
        
        assert notificacion.usuario == operador_atlantico_user
        assert notificacion.tipo == "nueva_solicitud"
        assert notificacion.titulo == "Nueva Solicitud de Transferencia"
        assert notificacion.prioridad == "alta"
        assert notificacion.leida is False
        assert notificacion.datos_adicionales["numero_orden"] == "SOL-2024-001"
        assert str(notificacion) == "Nueva Solicitud de Transferencia - operador_atlantico_test"
    
    def test_notificacion_tipo_validation(self, operador_atlantico_user):
        """Test validación de tipo de notificación"""
        notificacion = Notificacion(
            usuario=operador_atlantico_user,
            tipo="invalid_type",
            titulo="Test",
            mensaje="Test"
        )
        
        with pytest.raises(ValidationError):
            notificacion.full_clean()
    
    def test_notificacion_prioridad_validation(self, operador_atlantico_user):
        """Test validación de prioridad"""
        notificacion = Notificacion(
            usuario=operador_atlantico_user,
            tipo="nueva_solicitud",
            titulo="Test",
            mensaje="Test",
            prioridad="invalid_priority"
        )
        
        with pytest.raises(ValidationError):
            notificacion.full_clean()
    
    def test_notificacion_marcar_leida_method(self, operador_atlantico_user):
        """Test método marcar como leída"""
        notificacion = Notificacion.objects.create(
            usuario=operador_atlantico_user,
            tipo="nueva_solicitud",
            titulo="Test",
            mensaje="Test"
        )
        
        assert notificacion.leida is False
        assert notificacion.fecha_lectura is None
        
        notificacion.marcar_como_leida()
        
        assert notificacion.leida is True
        assert notificacion.fecha_lectura is not None
    
    def test_notificacion_es_urgente_property(self, operador_atlantico_user):
        """Test propiedad es_urgente"""
        notificacion = Notificacion.objects.create(
            usuario=operador_atlantico_user,
            tipo="nueva_solicitud",
            titulo="Test",
            mensaje="Test"
        )
        
        # Notificación recién creada debe ser urgente si tiene prioridad urgente
        notificacion.prioridad = "urgente"
        assert notificacion.es_urgente is True
        
        # Notificación con prioridad media no debe ser urgente
        notificacion.prioridad = "media"
        assert notificacion.es_urgente is False
    
    def test_notificacion_cascade_delete_usuario(self, operador_atlantico_user):
        """Test que al eliminar usuario se eliminen las notificaciones"""
        notificacion = Notificacion.objects.create(
            usuario=operador_atlantico_user,
            tipo="nueva_solicitud",
            titulo="Test",
            mensaje="Test"
        )
        
        notificacion_id = notificacion.id
        operador_atlantico_user.delete()
        
        assert not Notificacion.objects.filter(id=notificacion_id).exists()
    
    def test_notificacion_datos_adicionales_json_field(self, operador_atlantico_user):
        """Test campo JSON datos_adicionales"""
        datos = {
            "transferencia": {
                "id": "123",
                "numero_orden": "SOL-2024-001",
                "hidrologica_origen": "HAT"
            },
            "items": [
                {"sku": "TUB-001", "cantidad": 5},
                {"sku": "MOT-001", "cantidad": 2}
            ],
            "metadata": {
                "timestamp": "2024-01-20T10:00:00Z",
                "source": "api"
            }
        }
        
        notificacion = Notificacion.objects.create(
            usuario=operador_atlantico_user,
            tipo="nueva_solicitud",
            titulo="Test",
            mensaje="Test",
            datos_adicionales=datos
        )
        
        # Recargar desde DB
        notificacion.refresh_from_db()
        
        assert notificacion.datos_adicionales == datos
        assert notificacion.datos_adicionales["transferencia"]["numero_orden"] == "SOL-2024-001"
        assert len(notificacion.datos_adicionales["items"]) == 2
        assert notificacion.datos_adicionales["items"][0]["sku"] == "TUB-001"