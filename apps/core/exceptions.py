"""
Sistema centralizado de manejo de errores y códigos de error estándar.
"""
from enum import Enum
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Códigos de error estándar del sistema."""
    
    # Errores generales (1000-1999)
    GENERAL_ERROR = "ERR_1000"
    VALIDATION_ERROR = "ERR_1001"
    PERMISSION_DENIED = "ERR_1002"
    NOT_FOUND = "ERR_1003"
    AUTHENTICATION_FAILED = "ERR_1004"
    
    # Errores de organización (2000-2999)
    ENTE_RECTOR_NOT_FOUND = "ERR_2000"
    HIDROLOGICA_NOT_FOUND = "ERR_2001"
    ACUEDUCTO_NOT_FOUND = "ERR_2002"
    INVALID_ORGANIZATION_HIERARCHY = "ERR_2003"
    ORGANIZATION_INACTIVE = "ERR_2004"
    
    # Errores de inventario (3000-3999)
    ITEM_NOT_FOUND = "ERR_3000"
    ITEM_ALREADY_EXISTS = "ERR_3001"
    INVALID_ITEM_STATE = "ERR_3002"
    INVALID_ITEM_TYPE = "ERR_3003"
    ITEM_NOT_AVAILABLE = "ERR_3004"
    INSUFFICIENT_STOCK = "ERR_3005"
    ITEM_HISTORY_ERROR = "ERR_3006"
    
    # Errores de transferencias (4000-4999)
    TRANSFER_NOT_FOUND = "ERR_4000"
    TRANSFER_INVALID_STATE = "ERR_4001"
    TRANSFER_PERMISSION_DENIED = "ERR_4002"
    TRANSFER_ALREADY_APPROVED = "ERR_4003"
    TRANSFER_ALREADY_REJECTED = "ERR_4004"
    TRANSFER_CANNOT_CANCEL = "ERR_4005"
    INVALID_TRANSFER_WORKFLOW = "ERR_4006"
    
    # Errores de movimientos internos (5000-5999)
    MOVEMENT_NOT_FOUND = "ERR_5000"
    MOVEMENT_INVALID_STATE = "ERR_5001"
    MOVEMENT_SAME_LOCATION = "ERR_5002"
    MOVEMENT_INVALID_LOCATION = "ERR_5003"
    
    # Errores de QR y PDFs (6000-6999)
    QR_TOKEN_INVALID = "ERR_6000"
    QR_TOKEN_EXPIRED = "ERR_6001"
    QR_SIGNATURE_INVALID = "ERR_6002"
    PDF_GENERATION_FAILED = "ERR_6003"
    QR_ALREADY_USED = "ERR_6004"
    
    # Errores de notificaciones (7000-7999)
    NOTIFICATION_SEND_FAILED = "ERR_7000"
    NOTIFICATION_TEMPLATE_NOT_FOUND = "ERR_7001"
    NOTIFICATION_CHANNEL_ERROR = "ERR_7002"
    
    # Errores de multitenencia (8000-8999)
    MULTITENANCY_VIOLATION = "ERR_8000"
    CROSS_HIDROLOGICA_ACCESS = "ERR_8001"
    TENANT_CONTEXT_MISSING = "ERR_8002"


class BusinessLogicError(Exception):
    """Excepción base para errores de lógica de negocio."""
    
    def __init__(self, error_code: ErrorCode, message: str, details: dict = None):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ValidationError(BusinessLogicError):
    """Error de validación de datos."""
    pass


class PermissionError(BusinessLogicError):
    """Error de permisos."""
    pass


class NotFoundError(BusinessLogicError):
    """Error de recurso no encontrado."""
    pass


class StateError(BusinessLogicError):
    """Error de estado inválido."""
    pass


def get_error_message(error_code: ErrorCode, language: str = 'es') -> str:
    """Obtiene el mensaje de error localizado."""
    
    messages = {
        'es': {
            ErrorCode.GENERAL_ERROR: "Error general del sistema",
            ErrorCode.VALIDATION_ERROR: "Error de validación de datos",
            ErrorCode.PERMISSION_DENIED: "Permisos insuficientes",
            ErrorCode.NOT_FOUND: "Recurso no encontrado",
            ErrorCode.AUTHENTICATION_FAILED: "Autenticación fallida",
            
            ErrorCode.ENTE_RECTOR_NOT_FOUND: "Ente Rector no encontrado",
            ErrorCode.HIDROLOGICA_NOT_FOUND: "Hidrológica no encontrada",
            ErrorCode.ACUEDUCTO_NOT_FOUND: "Acueducto no encontrado",
            ErrorCode.INVALID_ORGANIZATION_HIERARCHY: "Jerarquía organizacional inválida",
            ErrorCode.ORGANIZATION_INACTIVE: "Organización inactiva",
            
            ErrorCode.ITEM_NOT_FOUND: "Ítem de inventario no encontrado",
            ErrorCode.ITEM_ALREADY_EXISTS: "El ítem ya existe",
            ErrorCode.INVALID_ITEM_STATE: "Estado de ítem inválido",
            ErrorCode.INVALID_ITEM_TYPE: "Tipo de ítem inválido",
            ErrorCode.ITEM_NOT_AVAILABLE: "Ítem no disponible",
            ErrorCode.INSUFFICIENT_STOCK: "Stock insuficiente",
            ErrorCode.ITEM_HISTORY_ERROR: "Error en historial del ítem",
            
            ErrorCode.TRANSFER_NOT_FOUND: "Transferencia no encontrada",
            ErrorCode.TRANSFER_INVALID_STATE: "Estado de transferencia inválido",
            ErrorCode.TRANSFER_PERMISSION_DENIED: "Sin permisos para esta transferencia",
            ErrorCode.TRANSFER_ALREADY_APPROVED: "Transferencia ya aprobada",
            ErrorCode.TRANSFER_ALREADY_REJECTED: "Transferencia ya rechazada",
            ErrorCode.TRANSFER_CANNOT_CANCEL: "No se puede cancelar la transferencia",
            ErrorCode.INVALID_TRANSFER_WORKFLOW: "Flujo de transferencia inválido",
            
            ErrorCode.MOVEMENT_NOT_FOUND: "Movimiento interno no encontrado",
            ErrorCode.MOVEMENT_INVALID_STATE: "Estado de movimiento inválido",
            ErrorCode.MOVEMENT_SAME_LOCATION: "La ubicación origen y destino son iguales",
            ErrorCode.MOVEMENT_INVALID_LOCATION: "Ubicación inválida",
            
            ErrorCode.QR_TOKEN_INVALID: "Token QR inválido",
            ErrorCode.QR_TOKEN_EXPIRED: "Token QR expirado",
            ErrorCode.QR_SIGNATURE_INVALID: "Firma digital QR inválida",
            ErrorCode.PDF_GENERATION_FAILED: "Error al generar PDF",
            ErrorCode.QR_ALREADY_USED: "Código QR ya utilizado",
            
            ErrorCode.NOTIFICATION_SEND_FAILED: "Error al enviar notificación",
            ErrorCode.NOTIFICATION_TEMPLATE_NOT_FOUND: "Plantilla de notificación no encontrada",
            ErrorCode.NOTIFICATION_CHANNEL_ERROR: "Error en canal de notificación",
            
            ErrorCode.MULTITENANCY_VIOLATION: "Violación de multitenencia",
            ErrorCode.CROSS_HIDROLOGICA_ACCESS: "Acceso entre hidrológicas no permitido",
            ErrorCode.TENANT_CONTEXT_MISSING: "Contexto de tenant faltante",
        }
    }
    
    return messages.get(language, {}).get(error_code, error_code.value)


def custom_exception_handler(exc, context):
    """Manejador personalizado de excepciones."""
    
    # Llamar al manejador por defecto primero
    response = exception_handler(exc, context)
    
    if isinstance(exc, BusinessLogicError):
        # Manejar errores de lógica de negocio
        error_data = {
            'error': {
                'code': exc.error_code.value,
                'message': exc.message,
                'details': exc.details
            }
        }
        
        # Determinar el código de estado HTTP
        status_code = status.HTTP_400_BAD_REQUEST
        if isinstance(exc, NotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, PermissionError):
            status_code = status.HTTP_403_FORBIDDEN
        elif isinstance(exc, ValidationError):
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        
        response = Response(error_data, status=status_code)
        
        # Log del error
        logger.error(
            f"Business Logic Error: {exc.error_code.value} - {exc.message}",
            extra={
                'error_code': exc.error_code.value,
                'details': exc.details,
                'context': context
            }
        )
    
    elif response is not None:
        # Personalizar respuestas de error estándar de DRF
        custom_response_data = {
            'error': {
                'code': ErrorCode.GENERAL_ERROR.value,
                'message': 'Error en la solicitud',
                'details': response.data
            }
        }
        
        # Casos específicos
        if response.status_code == status.HTTP_404_NOT_FOUND:
            custom_response_data['error']['code'] = ErrorCode.NOT_FOUND.value
            custom_response_data['error']['message'] = 'Recurso no encontrado'
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            custom_response_data['error']['code'] = ErrorCode.PERMISSION_DENIED.value
            custom_response_data['error']['message'] = 'Permisos insuficientes'
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            custom_response_data['error']['code'] = ErrorCode.AUTHENTICATION_FAILED.value
            custom_response_data['error']['message'] = 'Autenticación requerida'
        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            custom_response_data['error']['code'] = ErrorCode.VALIDATION_ERROR.value
            custom_response_data['error']['message'] = 'Error de validación'
        
        response.data = custom_response_data
    
    return response


class ErrorResponseMixin:
    """Mixin para ViewSets que proporciona métodos de respuesta de error estándar."""
    
    def error_response(self, error_code: ErrorCode, message: str = None, 
                      details: dict = None, status_code: int = None):
        """Crea una respuesta de error estándar."""
        
        if message is None:
            message = get_error_message(error_code)
        
        error_data = {
            'error': {
                'code': error_code.value,
                'message': message,
                'details': details or {}
            }
        }
        
        if status_code is None:
            status_code = status.HTTP_400_BAD_REQUEST
        
        return Response(error_data, status=status_code)
    
    def not_found_response(self, resource_name: str = "Recurso"):
        """Respuesta estándar para recurso no encontrado."""
        return self.error_response(
            ErrorCode.NOT_FOUND,
            f"{resource_name} no encontrado",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    def permission_denied_response(self, message: str = None):
        """Respuesta estándar para permisos denegados."""
        return self.error_response(
            ErrorCode.PERMISSION_DENIED,
            message or "No tiene permisos para realizar esta acción",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    def validation_error_response(self, details: dict):
        """Respuesta estándar para errores de validación."""
        return self.error_response(
            ErrorCode.VALIDATION_ERROR,
            "Error de validación de datos",
            details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )