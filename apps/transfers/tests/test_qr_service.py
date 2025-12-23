"""
Tests unitarios para el servicio de QR
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from django.utils import timezone

from apps.transfers.qr_service import QRService
from apps.transfers.models import EstadoTransferencia


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.services
class TestQRService:
    """Tests para QRService"""
    
    def test_generar_token_qr(self, transferencia_externa):
        """Test generar token QR"""
        token_data = QRService.generar_token_qr(transferencia_externa)
        
        assert 'token' in token_data
        assert 'signature' in token_data
        assert 'expires_at' in token_data
        assert 'qr_url' in token_data
        
        # Verificar que el token no esté vacío
        assert len(token_data['token']) > 0
        assert len(token_data['signature']) > 0
        
        # Verificar que la URL contenga los parámetros necesarios
        assert 'token=' in token_data['qr_url']
        assert 'signature=' in token_data['qr_url']
    
    def test_validar_token_qr_valid(self, transferencia_externa):
        """Test validar token QR válido"""
        # Generar token
        token_data = QRService.generar_token_qr(transferencia_externa)
        
        # Validar token
        validation_result = QRService.validar_token_qr(
            token_data['token'],
            token_data['signature']
        )
        
        assert validation_result['valid'] is True
        assert validation_result['transferencia_id'] == str(transferencia_externa.id)
        assert 'error' not in validation_result
    
    def test_validar_token_qr_invalid_signature(self, transferencia_externa):
        """Test validar token QR con firma inválida"""
        token_data = QRService.generar_token_qr(transferencia_externa)
        
        # Usar firma incorrecta
        validation_result = QRService.validar_token_qr(
            token_data['token'],
            'invalid_signature'
        )
        
        assert validation_result['valid'] is False
        assert 'error' in validation_result
        assert 'Firma digital inválida' in validation_result['error']
    
    def test_validar_token_qr_expired(self, transferencia_externa):
        """Test validar token QR expirado"""
        # Generar token con expiración en el pasado
        with patch('apps.transfers.qr_service.timezone.now') as mock_now:
            # Simular que estamos en el pasado para generar el token
            past_time = timezone.now() - timedelta(days=8)
            mock_now.return_value = past_time
            
            token_data = QRService.generar_token_qr(transferencia_externa)
        
        # Validar con tiempo actual (token debería estar expirado)
        validation_result = QRService.validar_token_qr(
            token_data['token'],
            token_data['signature']
        )
        
        assert validation_result['valid'] is False
        assert 'error' in validation_result
        assert 'Token expirado' in validation_result['error']
    
    def test_validar_token_qr_malformed(self):
        """Test validar token QR malformado"""
        validation_result = QRService.validar_token_qr(
            'invalid_token',
            'invalid_signature'
        )
        
        assert validation_result['valid'] is False
        assert 'error' in validation_result
    
    def test_obtener_info_transferencia_qr(self, transferencia_externa, item_tuberia_atlantico):
        """Test obtener información de transferencia desde QR"""
        # Agregar ítem a la transferencia
        from apps.transfers.models import ItemTransferencia
        ItemTransferencia.objects.create(
            transferencia=transferencia_externa,
            item=item_tuberia_atlantico,
            cantidad=5,
            cantidad_aprobada=3
        )
        
        # Generar token
        token_data = QRService.generar_token_qr(transferencia_externa)
        
        # Obtener información
        info = QRService.obtener_info_transferencia_qr(
            token_data['token'],
            token_data['signature']
        )
        
        assert info['valid'] is True
        assert 'transferencia' in info
        assert 'acciones_disponibles' in info
        
        # Verificar datos de transferencia
        transferencia_info = info['transferencia']
        assert transferencia_info['numero_orden'] == transferencia_externa.numero_orden
        assert transferencia_info['estado'] == transferencia_externa.estado
        assert transferencia_info['hidrologica_origen'] == transferencia_externa.hidrologica_origen.nombre
        assert transferencia_info['hidrologica_destino'] == transferencia_externa.hidrologica_destino.nombre
        
        # Verificar ítems
        assert len(transferencia_info['items']) == 1
        item_info = transferencia_info['items'][0]
        assert item_info['nombre'] == item_tuberia_atlantico.nombre
        assert item_info['cantidad_aprobada'] == 3
    
    def test_obtener_info_transferencia_qr_invalid_token(self):
        """Test obtener información con token inválido"""
        info = QRService.obtener_info_transferencia_qr(
            'invalid_token',
            'invalid_signature'
        )
        
        assert info['valid'] is False
        assert 'error' in info
    
    def test_confirmar_accion_qr_salida(self, transferencia_externa, operador_atlantico_user):
        """Test confirmar salida con QR"""
        # Cambiar estado a aprobada para poder confirmar salida
        transferencia_externa.estado = EstadoTransferencia.APROBADA
        transferencia_externa.save()
        
        # Generar token
        token_data = QRService.generar_token_qr(transferencia_externa)
        
        # Confirmar salida
        with patch('apps.notifications.services.notificar_transferencia_en_transito') as mock_notify:
            resultado = QRService.confirmar_accion_qr(
                token_data['token'],
                token_data['signature'],
                'confirmar_salida',
                operador_atlantico_user,
                'Salida confirmada'
            )
        
        assert resultado['success'] is True
        assert 'message' in resultado
        
        # Verificar que cambió el estado
        transferencia_externa.refresh_from_db()
        assert transferencia_externa.estado == EstadoTransferencia.EN_TRANSITO
        assert transferencia_externa.confirmado_salida_por == operador_atlantico_user
        
        mock_notify.assert_called_once()
    
    def test_confirmar_accion_qr_recepcion(self, transferencia_externa, operador_bolivar_user, item_tuberia_atlantico):
        """Test confirmar recepción con QR"""
        # Configurar transferencia en tránsito
        transferencia_externa.estado = EstadoTransferencia.EN_TRANSITO
        transferencia_externa.save()
        
        # Agregar ítem a la transferencia
        from apps.transfers.models import ItemTransferencia
        ItemTransferencia.objects.create(
            transferencia=transferencia_externa,
            item=item_tuberia_atlantico,
            cantidad=5
        )
        
        # Generar token
        token_data = QRService.generar_token_qr(transferencia_externa)
        
        # Confirmar recepción
        with patch('apps.notifications.services.notificar_transferencia_completada') as mock_notify:
            resultado = QRService.confirmar_accion_qr(
                token_data['token'],
                token_data['signature'],
                'confirmar_recepcion',
                operador_bolivar_user,
                'Recepción confirmada'
            )
        
        assert resultado['success'] is True
        
        # Verificar que cambió el estado
        transferencia_externa.refresh_from_db()
        assert transferencia_externa.estado == EstadoTransferencia.COMPLETADA
        assert transferencia_externa.confirmado_recepcion_por == operador_bolivar_user
        
        mock_notify.assert_called_once()
    
    def test_confirmar_accion_qr_invalid_token(self, operador_atlantico_user):
        """Test confirmar acción con token inválido"""
        resultado = QRService.confirmar_accion_qr(
            'invalid_token',
            'invalid_signature',
            'confirmar_salida',
            operador_atlantico_user
        )
        
        assert resultado['success'] is False
        assert 'error' in resultado
    
    def test_confirmar_accion_qr_invalid_action(self, transferencia_externa, operador_atlantico_user):
        """Test confirmar acción inválida"""
        token_data = QRService.generar_token_qr(transferencia_externa)
        
        resultado = QRService.confirmar_accion_qr(
            token_data['token'],
            token_data['signature'],
            'invalid_action',
            operador_atlantico_user
        )
        
        assert resultado['success'] is False
        assert 'error' in resultado
        assert 'Acción no válida' in resultado['error']
    
    def test_confirmar_accion_qr_wrong_state(self, transferencia_externa, operador_atlantico_user):
        """Test confirmar acción en estado incorrecto"""
        # Transferencia en estado solicitada, no se puede confirmar salida
        assert transferencia_externa.estado == EstadoTransferencia.SOLICITADA
        
        token_data = QRService.generar_token_qr(transferencia_externa)
        
        resultado = QRService.confirmar_accion_qr(
            token_data['token'],
            token_data['signature'],
            'confirmar_salida',
            operador_atlantico_user
        )
        
        assert resultado['success'] is False
        assert 'error' in resultado
    
    def test_confirmar_accion_qr_wrong_user(self, transferencia_externa, operador_bolivar_user):
        """Test confirmar salida con usuario de hidrológica incorrecta"""
        transferencia_externa.estado = EstadoTransferencia.APROBADA
        transferencia_externa.save()
        
        token_data = QRService.generar_token_qr(transferencia_externa)
        
        # Usuario de hidrológica destino no puede confirmar salida
        resultado = QRService.confirmar_accion_qr(
            token_data['token'],
            token_data['signature'],
            'confirmar_salida',
            operador_bolivar_user  # Usuario de hidrológica destino
        )
        
        assert resultado['success'] is False
        assert 'error' in resultado
    
    def test_generar_qr_code_image(self, transferencia_externa):
        """Test generar imagen de código QR"""
        token_data = QRService.generar_token_qr(transferencia_externa)
        
        # Generar imagen QR
        qr_image = QRService.generar_qr_code_image(token_data['qr_url'])
        
        assert qr_image is not None
        # Verificar que es una imagen PIL
        assert hasattr(qr_image, 'save')
        assert hasattr(qr_image, 'size')
    
    def test_obtener_acciones_disponibles_solicitada(self, transferencia_externa):
        """Test obtener acciones disponibles para transferencia solicitada"""
        acciones = QRService._obtener_acciones_disponibles(transferencia_externa)
        
        # En estado solicitada, no hay acciones disponibles
        assert len(acciones) == 0
    
    def test_obtener_acciones_disponibles_aprobada(self, transferencia_externa):
        """Test obtener acciones disponibles para transferencia aprobada"""
        transferencia_externa.estado = EstadoTransferencia.APROBADA
        transferencia_externa.save()
        
        acciones = QRService._obtener_acciones_disponibles(transferencia_externa)
        
        assert 'confirmar_salida' in acciones
        assert 'confirmar_recepcion' not in acciones
    
    def test_obtener_acciones_disponibles_en_transito(self, transferencia_externa):
        """Test obtener acciones disponibles para transferencia en tránsito"""
        transferencia_externa.estado = EstadoTransferencia.EN_TRANSITO
        transferencia_externa.save()
        
        acciones = QRService._obtener_acciones_disponibles(transferencia_externa)
        
        assert 'confirmar_recepcion' in acciones
        assert 'confirmar_salida' not in acciones
    
    def test_obtener_acciones_disponibles_completada(self, transferencia_externa):
        """Test obtener acciones disponibles para transferencia completada"""
        transferencia_externa.estado = EstadoTransferencia.COMPLETADA
        transferencia_externa.save()
        
        acciones = QRService._obtener_acciones_disponibles(transferencia_externa)
        
        # En estado completada, no hay acciones disponibles
        assert len(acciones) == 0