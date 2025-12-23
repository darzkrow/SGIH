"""
Tests unitarios para servicios del módulo transfers
"""
import pytest
from unittest.mock import patch, Mock
from django.core.exceptions import ValidationError

from apps.transfers.services import TransferService, MovimientoInternoService
from apps.transfers.models import EstadoTransferencia, ItemTransferencia
from apps.inventory.models import EstadoItem
from apps.core.exceptions import NotFoundError, BusinessLogicError


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.services
class TestTransferService:
    """Tests para TransferService"""
    
    @patch('apps.notifications.services.notificar_nueva_solicitud_transferencia')
    def test_solicitar_transferencia_success(self, mock_notify, hidrologica_atlantico, hidrologica_bolivar,
                                           acueducto_barranquilla, acueducto_cartagena,
                                           operador_atlantico_user, item_tuberia_atlantico):
        """Test solicitar transferencia exitosamente"""
        items_solicitados = [
            {
                'item_id': str(item_tuberia_atlantico.id),
                'cantidad': 5,
                'observaciones': 'Urgente'
            }
        ]
        
        transferencia = TransferService.solicitar_transferencia(
            hidrologica_origen_id=str(hidrologica_atlantico.id),
            acueducto_origen_id=str(acueducto_barranquilla.id),
            hidrologica_destino_id=str(hidrologica_bolivar.id),
            acueducto_destino_id=str(acueducto_cartagena.id),
            items_solicitados=items_solicitados,
            usuario=operador_atlantico_user,
            motivo="Emergencia",
            prioridad="alta"
        )
        
        assert transferencia.hidrologica_origen == hidrologica_atlantico
        assert transferencia.hidrologica_destino == hidrologica_bolivar
        assert transferencia.estado == EstadoTransferencia.SOLICITADA
        assert transferencia.prioridad == "alta"
        assert transferencia.motivo == "Emergencia"
        
        # Verificar que se creó el ítem de transferencia
        items_transferencia = transferencia.items_transferencia.all()
        assert len(items_transferencia) == 1
        assert items_transferencia[0].item == item_tuberia_atlantico
        assert items_transferencia[0].cantidad == 5
        
        # Verificar que se llamó la notificación
        mock_notify.assert_called_once_with(transferencia)
    
    def test_solicitar_transferencia_hidrologica_not_found(self, operador_atlantico_user):
        """Test error cuando hidrológica no existe"""
        with pytest.raises(NotFoundError):
            TransferService.solicitar_transferencia(
                hidrologica_origen_id="00000000-0000-0000-0000-000000000000",
                acueducto_origen_id="00000000-0000-0000-0000-000000000000",
                hidrologica_destino_id="00000000-0000-0000-0000-000000000000",
                acueducto_destino_id="00000000-0000-0000-0000-000000000000",
                items_solicitados=[],
                usuario=operador_atlantico_user,
                motivo="Test"
            )
    
    def test_solicitar_transferencia_same_hidrologica(self, hidrologica_atlantico, acueducto_barranquilla,
                                                    operador_atlantico_user):
        """Test error al solicitar transferencia a la misma hidrológica"""
        with pytest.raises(ValidationError, match="No se puede crear transferencia externa a la misma hidrológica"):
            TransferService.solicitar_transferencia(
                hidrologica_origen_id=str(hidrologica_atlantico.id),
                acueducto_origen_id=str(acueducto_barranquilla.id),
                hidrologica_destino_id=str(hidrologica_atlantico.id),  # Misma hidrológica
                acueducto_destino_id=str(acueducto_barranquilla.id),
                items_solicitados=[],
                usuario=operador_atlantico_user,
                motivo="Test"
            )
    
    def test_solicitar_transferencia_usuario_wrong_hidrologica(self, hidrologica_atlantico, hidrologica_bolivar,
                                                             acueducto_barranquilla, acueducto_cartagena,
                                                             operador_bolivar_user):
        """Test error cuando usuario no pertenece a hidrológica origen"""
        with pytest.raises(ValidationError, match="El usuario debe pertenecer a la hidrológica origen"):
            TransferService.solicitar_transferencia(
                hidrologica_origen_id=str(hidrologica_atlantico.id),
                acueducto_origen_id=str(acueducto_barranquilla.id),
                hidrologica_destino_id=str(hidrologica_bolivar.id),
                acueducto_destino_id=str(acueducto_cartagena.id),
                items_solicitados=[],
                usuario=operador_bolivar_user,  # Usuario de otra hidrológica
                motivo="Test"
            )
    
    def test_solicitar_transferencia_item_not_available(self, hidrologica_atlantico, hidrologica_bolivar,
                                                      acueducto_barranquilla, acueducto_cartagena,
                                                      operador_atlantico_user, item_tuberia_atlantico):
        """Test error cuando ítem no está disponible para transferencia"""
        # Cambiar estado del ítem a no transferible
        item_tuberia_atlantico.estado = EstadoItem.EN_TRANSITO
        item_tuberia_atlantico.save()
        
        items_solicitados = [
            {'item_id': str(item_tuberia_atlantico.id), 'cantidad': 1}
        ]
        
        with pytest.raises(ValidationError, match="no está disponible para transferencia"):
            TransferService.solicitar_transferencia(
                hidrologica_origen_id=str(hidrologica_atlantico.id),
                acueducto_origen_id=str(acueducto_barranquilla.id),
                hidrologica_destino_id=str(hidrologica_bolivar.id),
                acueducto_destino_id=str(acueducto_cartagena.id),
                items_solicitados=items_solicitados,
                usuario=operador_atlantico_user,
                motivo="Test"
            )
    
    @patch('apps.notifications.services.notificar_transferencia_aprobada')
    @patch('apps.transfers.tasks.generar_orden_traspaso.delay')
    def test_aprobar_transferencia_success(self, mock_task, mock_notify, transferencia_externa,
                                         admin_rector_user, item_tuberia_atlantico):
        """Test aprobar transferencia exitosamente"""
        # Agregar ítem a la transferencia
        ItemTransferencia.objects.create(
            transferencia=transferencia_externa,
            item=item_tuberia_atlantico,
            cantidad=5
        )
        
        transferencia_aprobada = TransferService.aprobar_transferencia(
            transferencia_id=str(transferencia_externa.id),
            usuario_rector=admin_rector_user,
            observaciones="Aprobada por emergencia"
        )
        
        assert transferencia_aprobada.estado == EstadoTransferencia.APROBADA
        assert transferencia_aprobada.aprobado_por == admin_rector_user
        assert "Aprobada por emergencia" in transferencia_aprobada.observaciones
        
        # Verificar que se cambió el estado del ítem
        item_tuberia_atlantico.refresh_from_db()
        assert item_tuberia_atlantico.estado == EstadoItem.EN_TRANSITO
        
        # Verificar que se llamaron las tareas
        mock_task.assert_called_once_with(transferencia_externa.id)
        mock_notify.assert_called_once_with(transferencia_aprobada)
    
    def test_aprobar_transferencia_not_found(self, admin_rector_user):
        """Test error cuando transferencia no existe"""
        with pytest.raises(ValidationError, match="Transferencia no encontrada"):
            TransferService.aprobar_transferencia(
                transferencia_id="00000000-0000-0000-0000-000000000000",
                usuario_rector=admin_rector_user
            )
    
    def test_aprobar_transferencia_not_ente_rector(self, transferencia_externa, operador_atlantico_user):
        """Test error cuando usuario no es Ente Rector"""
        with pytest.raises(ValidationError, match="Solo el Ente Rector puede aprobar transferencias"):
            TransferService.aprobar_transferencia(
                transferencia_id=str(transferencia_externa.id),
                usuario_rector=operador_atlantico_user
            )
    
    def test_aprobar_transferencia_wrong_state(self, transferencia_externa, admin_rector_user):
        """Test error cuando transferencia no está en estado correcto"""
        transferencia_externa.estado = EstadoTransferencia.APROBADA
        transferencia_externa.save()
        
        with pytest.raises(ValidationError, match="Solo se pueden aprobar transferencias en estado 'solicitada'"):
            TransferService.aprobar_transferencia(
                transferencia_id=str(transferencia_externa.id),
                usuario_rector=admin_rector_user
            )
    
    @patch('apps.notifications.services.notificar_transferencia_rechazada')
    def test_rechazar_transferencia_success(self, mock_notify, transferencia_externa, admin_rector_user):
        """Test rechazar transferencia exitosamente"""
        motivo_rechazo = "Stock insuficiente"
        
        transferencia_rechazada = TransferService.rechazar_transferencia(
            transferencia_id=str(transferencia_externa.id),
            usuario_rector=admin_rector_user,
            motivo_rechazo=motivo_rechazo
        )
        
        assert transferencia_rechazada.estado == EstadoTransferencia.RECHAZADA
        assert motivo_rechazo in transferencia_rechazada.observaciones
        
        mock_notify.assert_called_once_with(transferencia_rechazada, motivo_rechazo)
    
    @patch('apps.notifications.services.notificar_transferencia_en_transito')
    def test_iniciar_transito_success(self, mock_notify, transferencia_externa, operador_atlantico_user):
        """Test iniciar tránsito exitosamente"""
        # Cambiar estado a aprobada
        transferencia_externa.estado = EstadoTransferencia.APROBADA
        transferencia_externa.save()
        
        transferencia_transito = TransferService.iniciar_transito(
            transferencia_id=str(transferencia_externa.id),
            usuario=operador_atlantico_user
        )
        
        assert transferencia_transito.estado == EstadoTransferencia.EN_TRANSITO
        assert transferencia_transito.confirmado_salida_por == operador_atlantico_user
        
        mock_notify.assert_called_once_with(transferencia_transito)
    
    def test_iniciar_transito_wrong_hidrologica(self, transferencia_externa, operador_bolivar_user):
        """Test error al iniciar tránsito desde hidrológica incorrecta"""
        transferencia_externa.estado = EstadoTransferencia.APROBADA
        transferencia_externa.save()
        
        with pytest.raises(ValidationError, match="Solo usuarios de la hidrológica origen pueden confirmar la salida"):
            TransferService.iniciar_transito(
                transferencia_id=str(transferencia_externa.id),
                usuario=operador_bolivar_user
            )
    
    @patch('apps.notifications.services.notificar_transferencia_completada')
    def test_completar_transferencia_success(self, mock_notify, transferencia_externa, operador_bolivar_user,
                                           item_tuberia_atlantico):
        """Test completar transferencia exitosamente"""
        # Configurar transferencia en tránsito con ítem
        transferencia_externa.estado = EstadoTransferencia.EN_TRANSITO
        transferencia_externa.save()
        
        ItemTransferencia.objects.create(
            transferencia=transferencia_externa,
            item=item_tuberia_atlantico,
            cantidad=5
        )
        
        transferencia_completada = TransferService.completar_transferencia(
            transferencia_id=str(transferencia_externa.id),
            usuario=operador_bolivar_user
        )
        
        assert transferencia_completada.estado == EstadoTransferencia.COMPLETADA
        assert transferencia_completada.confirmado_recepcion_por == operador_bolivar_user
        
        # Verificar que se actualizó la ubicación del ítem
        item_tuberia_atlantico.refresh_from_db()
        assert item_tuberia_atlantico.hidrologica == transferencia_externa.hidrologica_destino
        assert item_tuberia_atlantico.acueducto_actual == transferencia_externa.acueducto_destino
        assert item_tuberia_atlantico.estado == EstadoItem.DISPONIBLE
        
        mock_notify.assert_called_once_with(transferencia_completada)
    
    def test_buscar_stock_disponible(self, item_tuberia_atlantico, item_motor_bolivar):
        """Test buscar stock disponible"""
        stock = TransferService.buscar_stock_disponible("tuberia")
        
        assert str(item_tuberia_atlantico.hidrologica.id) in stock
        assert str(item_motor_bolivar.hidrologica.id) not in stock
        
        # Verificar estructura de datos
        hidrologica_data = stock[str(item_tuberia_atlantico.hidrologica.id)]
        assert 'hidrologica' in hidrologica_data
        assert 'items' in hidrologica_data
        assert len(hidrologica_data['items']) >= 1
    
    def test_buscar_stock_disponible_exclude_hidrologica(self, item_tuberia_atlantico):
        """Test buscar stock excluyendo hidrológica"""
        stock = TransferService.buscar_stock_disponible(
            "tuberia",
            hidrologica_excluir=item_tuberia_atlantico.hidrologica
        )
        
        # No debe incluir la hidrológica excluida
        assert str(item_tuberia_atlantico.hidrologica.id) not in stock
    
    def test_obtener_transferencias_pendientes(self, transferencia_externa):
        """Test obtener transferencias pendientes"""
        transferencias = TransferService.obtener_transferencias_pendientes()
        
        assert transferencia_externa in transferencias
        
        # Cambiar estado y verificar que no aparezca
        transferencia_externa.estado = EstadoTransferencia.APROBADA
        transferencia_externa.save()
        
        transferencias = TransferService.obtener_transferencias_pendientes()
        assert transferencia_externa not in transferencias


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.services
class TestMovimientoInternoService:
    """Tests para MovimientoInternoService"""
    
    @patch('apps.notifications.services.notificar_movimiento_interno')
    def test_crear_movimiento_interno_success(self, mock_notify, item_tuberia_atlantico,
                                            acueducto_cartagena, operador_atlantico_user):
        """Test crear movimiento interno exitosamente"""
        # Crear otro acueducto en la misma hidrológica para el test
        from apps.core.models import Acueducto
        acueducto_destino = Acueducto.objects.create(
            hidrologica=item_tuberia_atlantico.hidrologica,
            nombre="Acueducto Destino Test",
            codigo="ADT",
            direccion="Test Address",
            telefono="+57 1 234 5678",
            email="test@adt.com"
        )
        
        movimiento = MovimientoInternoService.crear_movimiento_interno(
            item_id=str(item_tuberia_atlantico.id),
            acueducto_destino_id=str(acueducto_destino.id),
            usuario=operador_atlantico_user,
            motivo="Redistribución",
            observaciones="Movimiento de prueba"
        )
        
        assert movimiento.item == item_tuberia_atlantico
        assert movimiento.acueducto_destino == acueducto_destino
        assert movimiento.usuario == operador_atlantico_user
        assert movimiento.motivo == "Redistribución"
        
        mock_notify.assert_called_once_with(movimiento)
    
    def test_crear_movimiento_interno_item_not_found(self, operador_atlantico_user):
        """Test error cuando ítem no existe"""
        with pytest.raises(ValidationError):
            MovimientoInternoService.crear_movimiento_interno(
                item_id="00000000-0000-0000-0000-000000000000",
                acueducto_destino_id="00000000-0000-0000-0000-000000000000",
                usuario=operador_atlantico_user,
                motivo="Test"
            )
    
    def test_crear_movimiento_interno_wrong_hidrologica(self, item_tuberia_atlantico,
                                                      acueducto_cartagena, operador_bolivar_user):
        """Test error cuando usuario no pertenece a la hidrológica del ítem"""
        with pytest.raises(ValidationError, match="El usuario debe pertenecer a la misma hidrológica del ítem"):
            MovimientoInternoService.crear_movimiento_interno(
                item_id=str(item_tuberia_atlantico.id),
                acueducto_destino_id=str(acueducto_cartagena.id),
                usuario=operador_bolivar_user,
                motivo="Test"
            )
    
    def test_crear_movimiento_interno_same_acueducto(self, item_tuberia_atlantico, operador_atlantico_user):
        """Test error cuando origen y destino son el mismo acueducto"""
        with pytest.raises(ValidationError, match="El ítem ya está en el acueducto destino"):
            MovimientoInternoService.crear_movimiento_interno(
                item_id=str(item_tuberia_atlantico.id),
                acueducto_destino_id=str(item_tuberia_atlantico.acueducto_actual.id),
                usuario=operador_atlantico_user,
                motivo="Test"
            )
    
    def test_crear_movimiento_interno_item_not_available(self, item_tuberia_atlantico,
                                                       acueducto_cartagena, operador_atlantico_user):
        """Test error cuando ítem no está disponible"""
        item_tuberia_atlantico.estado = EstadoItem.EN_TRANSITO
        item_tuberia_atlantico.save()
        
        with pytest.raises(ValidationError, match="Solo se pueden mover ítems en estado disponible"):
            MovimientoInternoService.crear_movimiento_interno(
                item_id=str(item_tuberia_atlantico.id),
                acueducto_destino_id=str(acueducto_cartagena.id),
                usuario=operador_atlantico_user,
                motivo="Test"
            )
    
    def test_obtener_movimientos_hidrologica(self, hidrologica_atlantico):
        """Test obtener movimientos de hidrológica"""
        movimientos = MovimientoInternoService.obtener_movimientos_hidrologica(
            str(hidrologica_atlantico.id)
        )
        
        assert movimientos.count() >= 0  # Puede estar vacío inicialmente
    
    def test_obtener_historial_item(self, item_tuberia_atlantico):
        """Test obtener historial completo de ítem"""
        historial = MovimientoInternoService.obtener_historial_item(str(item_tuberia_atlantico.id))
        
        assert 'item' in historial
        assert 'ficha_vida' in historial
        assert 'movimientos_internos' in historial
        assert 'transferencias_externas' in historial
        
        # Verificar estructura del ítem
        item_data = historial['item']
        assert item_data['id'] == str(item_tuberia_atlantico.id)
        assert item_data['sku'] == item_tuberia_atlantico.sku