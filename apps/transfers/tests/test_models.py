"""
Tests unitarios para modelos del módulo transfers
"""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.transfers.models import (
    TransferenciaExterna, ItemTransferencia, MovimientoInterno,
    EstadoTransferencia
)


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.models
class TestTransferenciaExternaModel:
    """Tests para el modelo TransferenciaExterna"""
    
    def test_create_transferencia_externa(self, hidrologica_atlantico, hidrologica_bolivar,
                                        acueducto_barranquilla, acueducto_cartagena,
                                        operador_atlantico_user):
        """Test crear transferencia externa"""
        transferencia = TransferenciaExterna.objects.create(
            hidrologica_origen=hidrologica_atlantico,
            acueducto_origen=acueducto_barranquilla,
            hidrologica_destino=hidrologica_bolivar,
            acueducto_destino=acueducto_cartagena,
            solicitado_por=operador_atlantico_user,
            motivo="Test transfer",
            prioridad="media"
        )
        
        assert transferencia.hidrologica_origen == hidrologica_atlantico
        assert transferencia.hidrologica_destino == hidrologica_bolivar
        assert transferencia.estado == EstadoTransferencia.SOLICITADA
        assert transferencia.prioridad == "media"
        assert transferencia.numero_orden is not None
        assert transferencia.numero_orden.startswith("ORD")
        assert str(transferencia) == f"Orden {transferencia.numero_orden} - {transferencia.hidrologica_origen} → {transferencia.hidrologica_destino}"
    
    def test_transferencia_numero_orden_unique(self, hidrologica_atlantico, hidrologica_bolivar,
                                             acueducto_barranquilla, acueducto_cartagena,
                                             operador_atlantico_user):
        """Test que el número de orden sea único"""
        # Crear primera transferencia
        transferencia1 = TransferenciaExterna.objects.create(
            hidrologica_origen=hidrologica_atlantico,
            acueducto_origen=acueducto_barranquilla,
            hidrologica_destino=hidrologica_bolivar,
            acueducto_destino=acueducto_cartagena,
            solicitado_por=operador_atlantico_user,
            motivo="Test 1"
        )
        
        # Crear segunda transferencia
        transferencia2 = TransferenciaExterna.objects.create(
            hidrologica_origen=hidrologica_atlantico,
            acueducto_origen=acueducto_barranquilla,
            hidrologica_destino=hidrologica_bolivar,
            acueducto_destino=acueducto_cartagena,
            solicitado_por=operador_atlantico_user,
            motivo="Test 2"
        )
        
        # Los números de orden deben ser diferentes
        assert transferencia1.numero_orden != transferencia2.numero_orden
    
    def test_transferencia_same_hidrologica_validation(self, hidrologica_atlantico,
                                                     acueducto_barranquilla,
                                                     operador_atlantico_user):
        """Test que no permita transferencia a la misma hidrológica"""
        transferencia = TransferenciaExterna(
            hidrologica_origen=hidrologica_atlantico,
            acueducto_origen=acueducto_barranquilla,
            hidrologica_destino=hidrologica_atlantico,  # Misma hidrológica
            acueducto_destino=acueducto_barranquilla,
            solicitado_por=operador_atlantico_user,
            motivo="Test"
        )
        
        with pytest.raises(ValidationError):
            transferencia.clean()
    
    def test_transferencia_aprobar_method(self, transferencia_externa, admin_rector_user):
        """Test método aprobar transferencia"""
        assert transferencia_externa.estado == EstadoTransferencia.SOLICITADA
        
        transferencia_externa.aprobar(admin_rector_user)
        
        assert transferencia_externa.estado == EstadoTransferencia.APROBADA
        assert transferencia_externa.aprobado_por == admin_rector_user
        assert transferencia_externa.fecha_aprobacion is not None
    
    def test_transferencia_rechazar_method(self, transferencia_externa, admin_rector_user):
        """Test método rechazar transferencia"""
        motivo_rechazo = "Stock insuficiente"
        
        transferencia_externa.rechazar(admin_rector_user, motivo_rechazo)
        
        assert transferencia_externa.estado == EstadoTransferencia.RECHAZADA
        assert transferencia_externa.aprobado_por == admin_rector_user
        # rechazar no establece fecha_aprobacion, solo cambia estado
        assert motivo_rechazo in transferencia_externa.observaciones
    
    def test_transferencia_iniciar_transito_method(self, transferencia_externa, operador_atlantico_user):
        """Test método iniciar tránsito"""
        # Primero aprobar la transferencia
        transferencia_externa.estado = EstadoTransferencia.APROBADA
        transferencia_externa.save()
        
        transferencia_externa.iniciar_transito(operador_atlantico_user)
        
        assert transferencia_externa.estado == EstadoTransferencia.EN_TRANSITO
        assert transferencia_externa.fecha_inicio_transito is not None
        assert transferencia_externa.firma_origen is not None
        assert transferencia_externa.firma_origen['usuario'] == operador_atlantico_user.username
    
    def test_transferencia_completar_method(self, transferencia_externa, operador_bolivar_user):
        """Test método completar transferencia"""
        # Establecer estado en tránsito
        transferencia_externa.estado = EstadoTransferencia.EN_TRANSITO
        transferencia_externa.save()
        
        transferencia_externa.completar(operador_bolivar_user)
        
        assert transferencia_externa.estado == EstadoTransferencia.COMPLETADA
        assert transferencia_externa.fecha_completada is not None
        assert transferencia_externa.firma_destino is not None
        assert transferencia_externa.firma_destino['usuario'] == operador_bolivar_user.username
    
    def test_transferencia_invalid_state_transitions(self, transferencia_externa, admin_rector_user):
        """Test transiciones de estado inválidas"""
        # No se puede aprobar una transferencia ya rechazada
        transferencia_externa.estado = EstadoTransferencia.RECHAZADA
        transferencia_externa.save()
        
        with pytest.raises(ValidationError):
            transferencia_externa.aprobar(admin_rector_user)
        
        # No se puede completar sin estar en tránsito
        transferencia_externa.estado = EstadoTransferencia.SOLICITADA
        transferencia_externa.save()
        
        with pytest.raises(ValidationError):
            transferencia_externa.completar(admin_rector_user)
    
    def test_transferencia_puede_aprobarse_property(self, transferencia_externa):
        """Test propiedad puede_aprobarse"""
        # Puede aprobarse cuando está solicitada
        assert transferencia_externa.puede_aprobarse is True
        
        # No puede aprobarse cuando está aprobada
        transferencia_externa.estado = EstadoTransferencia.APROBADA
        assert transferencia_externa.puede_aprobarse is False
        
        # No puede aprobarse cuando está completada
        transferencia_externa.estado = EstadoTransferencia.COMPLETADA
        assert transferencia_externa.puede_aprobarse is False


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.models
class TestItemTransferenciaModel:
    """Tests para el modelo ItemTransferencia"""
    
    def test_create_item_transferencia(self, transferencia_externa, item_tuberia_atlantico):
        """Test crear ítem de transferencia"""
        item_transferencia = ItemTransferencia.objects.create(
            transferencia=transferencia_externa,
            item=item_tuberia_atlantico,
            cantidad=5,
            observaciones="Test item transfer"
        )
        
        assert item_transferencia.transferencia == transferencia_externa
        assert item_transferencia.item == item_tuberia_atlantico
        assert item_transferencia.cantidad == 5
        # ItemTransferencia no tiene campo cantidad_aprobada
        assert str(item_transferencia) == f"{item_tuberia_atlantico.sku} - {transferencia_externa.numero_orden}"
    
    def test_item_transferencia_unique_per_transfer(self, transferencia_externa, item_tuberia_atlantico):
        """Test que un ítem solo pueda estar una vez por transferencia"""
        # Crear primer ítem de transferencia
        ItemTransferencia.objects.create(
            transferencia=transferencia_externa,
            item=item_tuberia_atlantico,
            cantidad=3
        )
        
        # Intentar crear duplicado
        with pytest.raises(IntegrityError):
            ItemTransferencia.objects.create(
                transferencia=transferencia_externa,
                item=item_tuberia_atlantico,  # Mismo ítem
                cantidad=2
            )
    
    def test_item_transferencia_cantidad_validation(self, transferencia_externa, item_tuberia_atlantico):
        """Test validación de cantidad"""
        # Cantidad debe ser positiva (PositiveIntegerField permite 0 en Django)
        item_transferencia = ItemTransferencia(
            transferencia=transferencia_externa,
            item=item_tuberia_atlantico,
            cantidad=1  # Cantidad válida
        )
        
        # No debe lanzar excepción
        item_transferencia.full_clean()
        
        # Cantidad 0 es válida para PositiveIntegerField en Django
        item_transferencia.cantidad = 0
        item_transferencia.full_clean()  # No debe lanzar excepción


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.models
class TestMovimientoInternoModel:
    """Tests para el modelo MovimientoInterno"""
    
    def test_create_movimiento_interno(self, item_tuberia_atlantico, acueducto_barranquilla,
                                     acueducto_barranquilla_2, operador_atlantico_user):
        """Test crear movimiento interno"""
        movimiento = MovimientoInterno.objects.create(
            item=item_tuberia_atlantico,
            acueducto_origen=acueducto_barranquilla,
            acueducto_destino=acueducto_barranquilla_2,  # Usar acueducto de la misma hidrológica
            usuario=operador_atlantico_user,
            motivo="Redistribución",
            observaciones="Movimiento de prueba"
        )
        
        assert movimiento.item == item_tuberia_atlantico
        assert movimiento.acueducto_origen == acueducto_barranquilla
        assert movimiento.acueducto_destino == acueducto_barranquilla_2
        assert movimiento.usuario == operador_atlantico_user
        assert movimiento.motivo == "Redistribución"
        assert movimiento.fecha_movimiento is not None
        assert str(movimiento) == f"{item_tuberia_atlantico.sku}: {acueducto_barranquilla} → {acueducto_barranquilla_2}"
    
    def test_movimiento_interno_same_acueducto_validation(self, item_tuberia_atlantico,
                                                        acueducto_barranquilla,
                                                        operador_atlantico_user):
        """Test que no permita movimiento al mismo acueducto"""
        movimiento = MovimientoInterno(
            item=item_tuberia_atlantico,
            acueducto_origen=acueducto_barranquilla,
            acueducto_destino=acueducto_barranquilla,  # Mismo acueducto
            usuario=operador_atlantico_user,
            motivo="Test"
        )
        
        with pytest.raises(ValidationError):
            movimiento.clean()
    
    def test_movimiento_interno_different_hidrologica_validation(self, item_tuberia_atlantico,
                                                               acueducto_barranquilla,
                                                               acueducto_cartagena,
                                                               operador_atlantico_user):
        """Test que no permita movimiento entre diferentes hidrológicas"""
        # acueducto_cartagena pertenece a hidrologica_bolivar
        # item_tuberia_atlantico pertenece a hidrologica_atlantico
        
        movimiento = MovimientoInterno(
            item=item_tuberia_atlantico,
            acueducto_origen=acueducto_barranquilla,
            acueducto_destino=acueducto_cartagena,  # Diferente hidrológica
            usuario=operador_atlantico_user,
            motivo="Test"
        )
        
        with pytest.raises(ValidationError):
            movimiento.clean()
    
    def test_movimiento_interno_cascade_delete(self, item_tuberia_atlantico, acueducto_barranquilla,
                                             acueducto_barranquilla_2, operador_atlantico_user):
        """Test que al eliminar ítem se eliminen los movimientos"""
        movimiento = MovimientoInterno.objects.create(
            item=item_tuberia_atlantico,
            acueducto_origen=acueducto_barranquilla,
            acueducto_destino=acueducto_barranquilla_2,  # Usar acueducto de la misma hidrológica
            usuario=operador_atlantico_user,
            motivo="Test"
        )
        
        movimiento_id = movimiento.id
        item_tuberia_atlantico.delete()
        
        assert not MovimientoInterno.objects.filter(id=movimiento_id).exists()