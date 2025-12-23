"""
Tests unitarios para el sistema de excepciones personalizadas
"""
import pytest
from rest_framework.test import APIRequestFactory
from rest_framework.response import Response
from rest_framework import status
from unittest.mock import Mock

from apps.core.exceptions import (
    ErrorCode, BusinessLogicError, ValidationError, PermissionError,
    NotFoundError, StateError, get_error_message, custom_exception_handler,
    ErrorResponseMixin
)


@pytest.mark.unit
class TestErrorCode:
    """Tests para ErrorCode enum"""
    
    def test_error_codes_exist(self):
        """Test que existan los códigos de error principales"""
        assert ErrorCode.GENERAL_ERROR.value == "ERR_1000"
        assert ErrorCode.VALIDATION_ERROR.value == "ERR_1001"
        assert ErrorCode.ITEM_NOT_FOUND.value == "ERR_3000"
        assert ErrorCode.TRANSFER_NOT_FOUND.value == "ERR_4000"
        assert ErrorCode.QR_TOKEN_INVALID.value == "ERR_6000"
    
    def test_error_code_ranges(self):
        """Test que los códigos estén en los rangos correctos"""
        # Errores generales (1000-1999)
        assert ErrorCode.GENERAL_ERROR.value.startswith("ERR_1")
        assert ErrorCode.VALIDATION_ERROR.value.startswith("ERR_1")
        
        # Errores de organización (2000-2999)
        assert ErrorCode.ENTE_RECTOR_NOT_FOUND.value.startswith("ERR_2")
        assert ErrorCode.HIDROLOGICA_NOT_FOUND.value.startswith("ERR_2")
        
        # Errores de inventario (3000-3999)
        assert ErrorCode.ITEM_NOT_FOUND.value.startswith("ERR_3")
        assert ErrorCode.ITEM_ALREADY_EXISTS.value.startswith("ERR_3")
        
        # Errores de transferencias (4000-4999)
        assert ErrorCode.TRANSFER_NOT_FOUND.value.startswith("ERR_4")
        assert ErrorCode.TRANSFER_INVALID_STATE.value.startswith("ERR_4")


@pytest.mark.unit
class TestBusinessLogicError:
    """Tests para BusinessLogicError"""
    
    def test_create_business_logic_error(self):
        """Test crear error de lógica de negocio"""
        error = BusinessLogicError(
            ErrorCode.ITEM_NOT_FOUND,
            "Ítem no encontrado",
            {"item_id": "123"}
        )
        
        assert error.error_code == ErrorCode.ITEM_NOT_FOUND
        assert error.message == "Ítem no encontrado"
        assert error.details == {"item_id": "123"}
        assert str(error) == "Ítem no encontrado"
    
    def test_business_logic_error_without_details(self):
        """Test crear error sin detalles"""
        error = BusinessLogicError(
            ErrorCode.VALIDATION_ERROR,
            "Error de validación"
        )
        
        assert error.details == {}
    
    def test_validation_error_inheritance(self):
        """Test que ValidationError herede de BusinessLogicError"""
        error = ValidationError(
            ErrorCode.VALIDATION_ERROR,
            "Datos inválidos"
        )
        
        assert isinstance(error, BusinessLogicError)
        assert error.error_code == ErrorCode.VALIDATION_ERROR
    
    def test_permission_error_inheritance(self):
        """Test que PermissionError herede de BusinessLogicError"""
        error = PermissionError(
            ErrorCode.PERMISSION_DENIED,
            "Acceso denegado"
        )
        
        assert isinstance(error, BusinessLogicError)
        assert error.error_code == ErrorCode.PERMISSION_DENIED
    
    def test_not_found_error_inheritance(self):
        """Test que NotFoundError herede de BusinessLogicError"""
        error = NotFoundError(
            ErrorCode.ITEM_NOT_FOUND,
            "Ítem no encontrado"
        )
        
        assert isinstance(error, BusinessLogicError)
        assert error.error_code == ErrorCode.ITEM_NOT_FOUND
    
    def test_state_error_inheritance(self):
        """Test que StateError herede de BusinessLogicError"""
        error = StateError(
            ErrorCode.TRANSFER_INVALID_STATE,
            "Estado de transferencia inválido"
        )
        
        assert isinstance(error, BusinessLogicError)
        assert error.error_code == ErrorCode.TRANSFER_INVALID_STATE


@pytest.mark.unit
class TestGetErrorMessage:
    """Tests para get_error_message"""
    
    def test_get_error_message_spanish(self):
        """Test obtener mensaje en español"""
        message = get_error_message(ErrorCode.ITEM_NOT_FOUND, 'es')
        assert message == "Ítem de inventario no encontrado"
        
        message = get_error_message(ErrorCode.VALIDATION_ERROR, 'es')
        assert message == "Error de validación de datos"
    
    def test_get_error_message_default_language(self):
        """Test obtener mensaje con idioma por defecto"""
        message = get_error_message(ErrorCode.ITEM_NOT_FOUND)
        assert message == "Ítem de inventario no encontrado"
    
    def test_get_error_message_unknown_code(self):
        """Test obtener mensaje para código desconocido"""
        # Crear un código de error ficticio
        class FakeErrorCode:
            value = "ERR_9999"
        
        fake_code = FakeErrorCode()
        message = get_error_message(fake_code, 'es')
        assert message == "ERR_9999"  # Debe retornar el código si no encuentra mensaje
    
    def test_get_error_message_unknown_language(self):
        """Test obtener mensaje para idioma desconocido"""
        message = get_error_message(ErrorCode.ITEM_NOT_FOUND, 'fr')
        assert message == ErrorCode.ITEM_NOT_FOUND.value  # Debe retornar el código


@pytest.mark.unit
class TestCustomExceptionHandler:
    """Tests para custom_exception_handler"""
    
    def setup_method(self):
        self.factory = APIRequestFactory()
    
    def test_handle_business_logic_error(self):
        """Test manejar BusinessLogicError"""
        request = self.factory.get('/')
        context = {'request': request}
        
        error = BusinessLogicError(
            ErrorCode.ITEM_NOT_FOUND,
            "Ítem no encontrado",
            {"item_id": "123"}
        )
        
        response = custom_exception_handler(error, context)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error']['code'] == "ERR_3000"
        assert response.data['error']['message'] == "Ítem no encontrado"
        assert response.data['error']['details'] == {"item_id": "123"}
    
    def test_handle_not_found_error(self):
        """Test manejar NotFoundError"""
        request = self.factory.get('/')
        context = {'request': request}
        
        error = NotFoundError(
            ErrorCode.ITEM_NOT_FOUND,
            "Ítem no encontrado"
        )
        
        response = custom_exception_handler(error, context)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['error']['code'] == "ERR_3000"
    
    def test_handle_permission_error(self):
        """Test manejar PermissionError"""
        request = self.factory.get('/')
        context = {'request': request}
        
        error = PermissionError(
            ErrorCode.PERMISSION_DENIED,
            "Acceso denegado"
        )
        
        response = custom_exception_handler(error, context)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['error']['code'] == "ERR_1002"
    
    def test_handle_validation_error(self):
        """Test manejar ValidationError"""
        request = self.factory.get('/')
        context = {'request': request}
        
        error = ValidationError(
            ErrorCode.VALIDATION_ERROR,
            "Datos inválidos"
        )
        
        response = custom_exception_handler(error, context)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.data['error']['code'] == "ERR_1001"
    
    def test_handle_standard_drf_error(self):
        """Test manejar errores estándar de DRF"""
        from rest_framework.exceptions import ValidationError as DRFValidationError
        
        request = self.factory.get('/')
        context = {'request': request}
        
        # Simular respuesta de DRF
        mock_response = Mock()
        mock_response.status_code = status.HTTP_400_BAD_REQUEST
        mock_response.data = {'field': ['This field is required.']}
        
        # Simular que exception_handler de DRF retorna una respuesta
        with pytest.MonkeyPatch().context() as m:
            def mock_drf_handler(exc, context):
                return mock_response
            
            m.setattr('apps.core.exceptions.exception_handler', mock_drf_handler)
            
            error = DRFValidationError("Validation error")
            response = custom_exception_handler(error, context)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert 'error' in response.data
            assert response.data['error']['code'] == "ERR_1001"
    
    def test_handle_unknown_error(self):
        """Test manejar error desconocido"""
        request = self.factory.get('/')
        context = {'request': request}
        
        # Error que no es BusinessLogicError y DRF no maneja
        error = ValueError("Unknown error")
        
        response = custom_exception_handler(error, context)
        
        # Debe retornar None para que Django maneje el error
        assert response is None


@pytest.mark.unit
class TestErrorResponseMixin:
    """Tests para ErrorResponseMixin"""
    
    def setup_method(self):
        self.mixin = ErrorResponseMixin()
    
    def test_error_response(self):
        """Test crear respuesta de error estándar"""
        response = self.mixin.error_response(
            ErrorCode.ITEM_NOT_FOUND,
            "Ítem no encontrado",
            {"item_id": "123"},
            status.HTTP_404_NOT_FOUND
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['error']['code'] == "ERR_3000"
        assert response.data['error']['message'] == "Ítem no encontrado"
        assert response.data['error']['details'] == {"item_id": "123"}
    
    def test_error_response_default_message(self):
        """Test respuesta de error con mensaje por defecto"""
        response = self.mixin.error_response(ErrorCode.ITEM_NOT_FOUND)
        
        assert response.data['error']['message'] == "Ítem de inventario no encontrado"
    
    def test_error_response_default_status(self):
        """Test respuesta de error con status por defecto"""
        response = self.mixin.error_response(ErrorCode.ITEM_NOT_FOUND)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_not_found_response(self):
        """Test respuesta estándar para recurso no encontrado"""
        response = self.mixin.not_found_response("Ítem")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['error']['code'] == "ERR_1003"
        assert response.data['error']['message'] == "Ítem no encontrado"
    
    def test_not_found_response_default(self):
        """Test respuesta no encontrado con mensaje por defecto"""
        response = self.mixin.not_found_response()
        
        assert response.data['error']['message'] == "Recurso no encontrado"
    
    def test_permission_denied_response(self):
        """Test respuesta estándar para permisos denegados"""
        response = self.mixin.permission_denied_response("Sin permisos para esta acción")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['error']['code'] == "ERR_1002"
        assert response.data['error']['message'] == "Sin permisos para esta acción"
    
    def test_permission_denied_response_default(self):
        """Test respuesta permisos denegados con mensaje por defecto"""
        response = self.mixin.permission_denied_response()
        
        assert response.data['error']['message'] == "No tiene permisos para realizar esta acción"
    
    def test_validation_error_response(self):
        """Test respuesta estándar para errores de validación"""
        details = {
            'sku': ['Este campo es requerido.'],
            'nombre': ['Este campo no puede estar vacío.']
        }
        
        response = self.mixin.validation_error_response(details)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.data['error']['code'] == "ERR_1001"
        assert response.data['error']['message'] == "Error de validación de datos"
        assert response.data['error']['details'] == details