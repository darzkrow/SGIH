"""
Tests unitarios para servicios del módulo inventory
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, Mock

from apps.inventory.services import InventoryService, ItemHistoryService
from apps.inventory.models import EstadoItem


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.services
class TestInventoryService:
    """Tests para InventoryService"""
    
    def test_cambiar_estado_item(self, item_tuberia_atlantico, operador_atlantico_user):
        """Test cambiar estado de ítem"""
        estado_inicial = item_tuberia_atlantico.estado
        
        InventoryService.cambiar_estado_item(
            item=item_tuberia_atlantico,
            nuevo_estado=EstadoItem.EN_MANTENIMIENTO,
            usuario=operador_atlantico_user,
            motivo="Mantenimiento programado",
            observaciones="Revisión técnica"
        )
        
        # Verificar cambio de estado
        item_tuberia_atlantico.refresh_from_db()
        assert item_tuberia_atlantico.estado == EstadoItem.EN_MANTENIMIENTO
        
        # Verificar registro en historial
        historial = item_tuberia_atlantico.historial_movimientos
        ultimo_evento = historial[-1]
        
        assert ultimo_evento["tipo"] == "cambio_estado"
        assert ultimo_evento["estado_anterior"] == estado_inicial
        assert ultimo_evento["estado_nuevo"] == EstadoItem.EN_MANTENIMIENTO
        assert ultimo_evento["motivo"] == "Mantenimiento programado"
        assert ultimo_evento["observaciones"] == "Revisión técnica"
        assert ultimo_evento["usuario"]["username"] == operador_atlantico_user.username
    
    def test_cambiar_estado_item_mismo_estado(self, item_tuberia_atlantico, operador_atlantico_user):
        """Test que no permita cambiar al mismo estado"""
        estado_actual = item_tuberia_atlantico.estado
        
        with pytest.raises(ValueError, match="El ítem ya está en ese estado"):
            InventoryService.cambiar_estado_item(
                item=item_tuberia_atlantico,
                nuevo_estado=estado_actual,
                usuario=operador_atlantico_user
            )
    
    def test_cambiar_estado_item_transicion_invalida(self, item_tuberia_atlantico, operador_atlantico_user):
        """Test validación de transiciones de estado"""
        # Cambiar a estado dado_baja (final)
        item_tuberia_atlantico.estado = EstadoItem.DADO_BAJA
        item_tuberia_atlantico.save()
        
        # No debe permitir cambiar desde estado final
        with pytest.raises(ValueError, match="No se puede cambiar el estado desde"):
            InventoryService.cambiar_estado_item(
                item=item_tuberia_atlantico,
                nuevo_estado=EstadoItem.DISPONIBLE,
                usuario=operador_atlantico_user
            )
    
    def test_obtener_estadisticas_hidrologica(self, hidrologica_atlantico, item_tuberia_atlantico):
        """Test obtener estadísticas de hidrológica"""
        estadisticas = InventoryService.obtener_estadisticas_hidrologica(hidrologica_atlantico)
        
        assert "total_items" in estadisticas
        assert "por_tipo" in estadisticas
        assert "por_estado" in estadisticas
        assert "valor_total" in estadisticas
        
        assert estadisticas["total_items"] >= 1
        assert "tuberia" in estadisticas["por_tipo"]
        assert "disponible" in estadisticas["por_estado"]
    
    def test_buscar_items_disponibles(self, item_tuberia_atlantico, item_motor_bolivar):
        """Test buscar ítems disponibles"""
        # Buscar por tipo
        items_tuberia = InventoryService.buscar_items_disponibles(tipo="tuberia")
        assert item_tuberia_atlantico in items_tuberia
        assert item_motor_bolivar not in items_tuberia
        
        # Buscar por hidrológica
        items_atlantico = InventoryService.buscar_items_disponibles(
            hidrologica=item_tuberia_atlantico.hidrologica
        )
        assert item_tuberia_atlantico in items_atlantico
        assert item_motor_bolivar not in items_atlantico
    
    def test_validar_disponibilidad_transferencia(self, item_tuberia_atlantico):
        """Test validar disponibilidad para transferencia"""
        # Ítem disponible debe ser válido
        assert InventoryService.validar_disponibilidad_transferencia(item_tuberia_atlantico) is True
        
        # Cambiar a estado no transferible
        item_tuberia_atlantico.estado = EstadoItem.EN_TRANSITO
        item_tuberia_atlantico.save()
        
        assert InventoryService.validar_disponibilidad_transferencia(item_tuberia_atlantico) is False


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.services
class TestItemHistoryService:
    """Tests para ItemHistoryService"""
    
    def test_registrar_creacion(self, item_tuberia_atlantico, operador_atlantico_user):
        """Test registrar evento de creación"""
        evento = ItemHistoryService.registrar_creacion(
            item=item_tuberia_atlantico,
            usuario=operador_atlantico_user,
            datos_adicionales={"proveedor": "Test Provider"},
            observaciones="Ítem creado para testing"
        )
        
        assert evento["tipo"] == "creacion"
        assert evento["usuario"]["username"] == operador_atlantico_user.username
        assert evento["datos_adicionales"]["proveedor"] == "Test Provider"
        assert evento["observaciones"] == "Ítem creado para testing"
        assert "id" in evento
        assert "fecha" in evento
        assert "timestamp" in evento
    
    def test_registrar_cambio_estado(self, item_tuberia_atlantico, operador_atlantico_user):
        """Test registrar cambio de estado"""
        estado_anterior = item_tuberia_atlantico.estado
        nuevo_estado = EstadoItem.EN_MANTENIMIENTO
        
        evento = ItemHistoryService.registrar_cambio_estado(
            item=item_tuberia_atlantico,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            usuario=operador_atlantico_user,
            motivo="Mantenimiento",
            observaciones="Revisión técnica"
        )
        
        assert evento["tipo"] == "cambio_estado"
        assert evento["estado_anterior"] == estado_anterior
        assert evento["estado_nuevo"] == nuevo_estado
        assert evento["motivo"] == "Mantenimiento"
        assert evento["observaciones"] == "Revisión técnica"
    
    def test_registrar_movimiento_interno(self, item_tuberia_atlantico, acueducto_cartagena, 
                                        operador_atlantico_user):
        """Test registrar movimiento interno"""
        acueducto_origen = item_tuberia_atlantico.acueducto_actual
        
        evento = ItemHistoryService.registrar_movimiento_interno(
            item=item_tuberia_atlantico,
            acueducto_origen=acueducto_origen,
            acueducto_destino=acueducto_cartagena,
            usuario=operador_atlantico_user,
            motivo="Redistribución",
            observaciones="Movimiento de prueba"
        )
        
        assert evento["tipo"] == "movimiento_interno"
        assert evento["ubicacion_origen"]["acueducto"]["nombre"] == acueducto_origen.nombre
        assert evento["ubicacion_destino"]["acueducto"]["nombre"] == acueducto_cartagena.nombre
        assert evento["motivo"] == "Redistribución"
    
    def test_registrar_transferencia_externa(self, item_tuberia_atlantico, hidrologica_bolivar,
                                           acueducto_barranquilla, acueducto_cartagena,
                                           operador_atlantico_user):
        """Test registrar transferencia externa"""
        evento = ItemHistoryService.registrar_transferencia_externa(
            item=item_tuberia_atlantico,
            hidrologica_origen=item_tuberia_atlantico.hidrologica,
            hidrologica_destino=hidrologica_bolivar,
            acueducto_origen=acueducto_barranquilla,
            acueducto_destino=acueducto_cartagena,
            numero_orden="TEST-001",
            usuario=operador_atlantico_user,
            observaciones="Transferencia de prueba"
        )
        
        assert evento["tipo"] == "transferencia_externa"
        assert evento["numero_orden"] == "TEST-001"
        assert evento["ubicacion_origen"]["hidrologica"]["codigo"] == "HAT"
        assert evento["ubicacion_destino"]["hidrologica"]["codigo"] == "HBL"
    
    def test_registrar_mantenimiento(self, item_tuberia_atlantico, operador_atlantico_user):
        """Test registrar evento de mantenimiento"""
        fecha_inicio = datetime.now(timezone.utc)
        fecha_fin = datetime.now(timezone.utc)
        
        evento = ItemHistoryService.registrar_mantenimiento(
            item=item_tuberia_atlantico,
            tipo_mantenimiento="preventivo",
            usuario=operador_atlantico_user,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            observaciones="Mantenimiento preventivo"
        )
        
        assert evento["tipo"] == "mantenimiento"
        assert evento["tipo_mantenimiento"] == "preventivo"
        assert evento["fecha_inicio"] is not None
        assert evento["fecha_fin"] is not None
    
    def test_obtener_historial_completo(self, item_tuberia_atlantico):
        """Test obtener historial completo"""
        historial = ItemHistoryService.obtener_historial_completo(item_tuberia_atlantico)
        
        assert isinstance(historial, list)
        assert len(historial) >= 1  # Al menos evento de creación
        
        # Verificar estructura de eventos
        for evento in historial:
            assert "id" in evento
            assert "tipo" in evento
            assert "fecha" in evento
            assert "timestamp" in evento
    
    def test_obtener_historial_por_tipo(self, item_tuberia_atlantico, operador_atlantico_user):
        """Test obtener historial filtrado por tipo"""
        # Agregar evento de cambio de estado
        ItemHistoryService.registrar_cambio_estado(
            item=item_tuberia_atlantico,
            estado_anterior="disponible",
            estado_nuevo="en_mantenimiento",
            usuario=operador_atlantico_user
        )
        
        # Filtrar por tipo
        eventos_cambio = ItemHistoryService.obtener_historial_por_tipo(
            item_tuberia_atlantico, "cambio_estado"
        )
        
        assert len(eventos_cambio) >= 1
        for evento in eventos_cambio:
            assert evento["tipo"] == "cambio_estado"
    
    def test_obtener_historial_por_usuario(self, item_tuberia_atlantico, operador_atlantico_user):
        """Test obtener historial filtrado por usuario"""
        # Agregar evento
        ItemHistoryService.registrar_cambio_estado(
            item=item_tuberia_atlantico,
            estado_anterior="disponible",
            estado_nuevo="en_mantenimiento",
            usuario=operador_atlantico_user
        )
        
        # Filtrar por usuario
        eventos_usuario = ItemHistoryService.obtener_historial_por_usuario(
            item_tuberia_atlantico, str(operador_atlantico_user.id)
        )
        
        assert len(eventos_usuario) >= 1
        for evento in eventos_usuario:
            assert evento["usuario"]["id"] == str(operador_atlantico_user.id)
    
    def test_generar_reporte_trazabilidad(self, item_tuberia_atlantico, operador_atlantico_user):
        """Test generar reporte de trazabilidad"""
        # Agregar algunos eventos
        ItemHistoryService.registrar_cambio_estado(
            item=item_tuberia_atlantico,
            estado_anterior="disponible",
            estado_nuevo="en_mantenimiento",
            usuario=operador_atlantico_user
        )
        
        reporte = ItemHistoryService.generar_reporte_trazabilidad(item_tuberia_atlantico)
        
        assert "item" in reporte
        assert "resumen" in reporte
        assert "historial_completo" in reporte
        assert "estadisticas" in reporte
        
        # Verificar estructura del resumen
        resumen = reporte["resumen"]
        assert "total_eventos" in resumen
        assert "primer_evento" in resumen
        assert "ultimo_evento" in resumen
        assert "ubicaciones_historicas" in resumen
        assert "estados_historicos" in resumen
        
        # Verificar estadísticas
        estadisticas = reporte["estadisticas"]
        assert "eventos_por_tipo" in estadisticas
        assert "eventos_por_usuario" in estadisticas
        assert "tiempo_en_estados" in estadisticas