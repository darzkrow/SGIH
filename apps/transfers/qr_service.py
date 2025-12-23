"""
Servicio para generación y validación de códigos QR
"""
import uuid
import hashlib
import hmac
import qrcode
from datetime import datetime, timedelta
from io import BytesIO
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import TransferenciaExterna


class QRService:
    """
    Servicio para gestión de códigos QR y URLs firmadas
    """
    
    @staticmethod
    def generar_token_seguro():
        """
        Generar token único y seguro para QR
        
        Returns:
            str: Token único de 32 caracteres
        """
        return str(uuid.uuid4()).replace('-', '')
    
    @staticmethod
    def crear_url_firmada(transferencia_id, token, expiration_hours=24):
        """
        Crear URL firmada digitalmente para validación QR
        
        Args:
            transferencia_id: ID de la transferencia
            token: Token único
            expiration_hours: Horas de expiración (default 24)
        
        Returns:
            str: URL firmada digitalmente
        """
        # Calcular timestamp de expiración
        expiration_time = timezone.now() + timedelta(hours=expiration_hours)
        timestamp = int(expiration_time.timestamp())
        
        # Datos a firmar
        data = f"{transferencia_id}:{token}:{timestamp}"
        
        # Crear firma HMAC-SHA256
        secret_key = getattr(settings, 'SECRET_KEY', 'default-secret')
        signature = hmac.new(
            secret_key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Construir URL base
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        
        # URL completa con parámetros
        url = (f"{base_url}/qr/validate?"
               f"token={token}&"
               f"sig={signature}&"
               f"ts={timestamp}&"
               f"id={transferencia_id}")
        
        return url
    
    @staticmethod
    def validar_firma_url(token, signature, timestamp, transferencia_id):
        """
        Validar la autenticidad de una URL firmada
        
        Args:
            token: Token del QR
            signature: Firma digital
            timestamp: Timestamp de expiración
            transferencia_id: ID de la transferencia
        
        Returns:
            dict: Resultado de la validación
        """
        try:
            # Verificar expiración
            current_time = int(timezone.now().timestamp())
            if current_time > int(timestamp):
                return {
                    'valido': False, 
                    'error': 'Token expirado',
                    'codigo_error': 'TOKEN_EXPIRED'
                }
            
            # Reconstruir datos originales
            data = f"{transferencia_id}:{token}:{timestamp}"
            
            # Calcular firma esperada
            secret_key = getattr(settings, 'SECRET_KEY', 'default-secret')
            expected_signature = hmac.new(
                secret_key.encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Comparar firmas de forma segura
            if not hmac.compare_digest(signature, expected_signature):
                return {
                    'valido': False, 
                    'error': 'Firma digital inválida',
                    'codigo_error': 'INVALID_SIGNATURE'
                }
            
            return {
                'valido': True,
                'mensaje': 'Firma válida'
            }
            
        except Exception as e:
            return {
                'valido': False, 
                'error': f'Error de validación: {str(e)}',
                'codigo_error': 'VALIDATION_ERROR'
            }
    
    @staticmethod
    def generar_codigo_qr(url, size=10, border=4):
        """
        Generar código QR para una URL
        
        Args:
            url: URL a codificar
            size: Tamaño de cada "caja" del QR
            border: Tamaño del borde
        
        Returns:
            BytesIO: Buffer con imagen PNG del QR
        """
        # Configurar QR
        qr = qrcode.QRCode(
            version=1,  # Controla el tamaño del QR
            error_correction=qrcode.constants.ERROR_CORRECT_M,  # ~15% de corrección de errores
            box_size=size,
            border=border,
        )
        
        # Agregar datos
        qr.add_data(url)
        qr.make(fit=True)
        
        # Crear imagen
        img = qr.make_image(
            fill_color="black", 
            back_color="white"
        )
        
        # Convertir a buffer
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def validar_qr_token(token, signature=None, timestamp=None, transferencia_id=None):
        """
        Validar token QR completo y retornar información de transferencia
        
        Args:
            token: Token del QR
            signature: Firma digital (opcional si se valida por separado)
            timestamp: Timestamp (opcional si se valida por separado)
            transferencia_id: ID de transferencia (opcional si se valida por separado)
        
        Returns:
            dict: Información completa de la transferencia o error
        """
        try:
            # Si se proporcionan parámetros de firma, validar primero
            if signature and timestamp and transferencia_id:
                validacion_firma = QRService.validar_firma_url(
                    token, signature, timestamp, transferencia_id
                )
                if not validacion_firma['valido']:
                    return validacion_firma
            
            # Buscar transferencia por token
            try:
                transferencia = TransferenciaExterna.objects.get(qr_token=token)
            except TransferenciaExterna.DoesNotExist:
                return {
                    'valido': False,
                    'error': 'Token QR no encontrado',
                    'codigo_error': 'TOKEN_NOT_FOUND'
                }
            
            # Verificar que la URL firmada sea válida
            if transferencia.url_firmada:
                # Extraer parámetros de la URL si no se proporcionaron
                if not (signature and timestamp and transferencia_id):
                    url_params = QRService._extraer_parametros_url(transferencia.url_firmada)
                    if url_params:
                        validacion_firma = QRService.validar_firma_url(
                            token, 
                            url_params['signature'], 
                            url_params['timestamp'], 
                            str(transferencia.id)
                        )
                        if not validacion_firma['valido']:
                            return validacion_firma
            
            # Retornar información completa de la transferencia
            return {
                'valido': True,
                'transferencia': {
                    'id': str(transferencia.id),
                    'numero_orden': transferencia.numero_orden,
                    'estado': transferencia.estado,
                    'estado_display': transferencia.get_estado_display(),
                    'prioridad': transferencia.prioridad,
                    'prioridad_display': transferencia.get_prioridad_display(),
                    
                    # Información de origen y destino
                    'origen': {
                        'hidrologica': {
                            'id': str(transferencia.hidrologica_origen.id),
                            'nombre': transferencia.hidrologica_origen.nombre,
                            'codigo': transferencia.hidrologica_origen.codigo
                        },
                        'acueducto': {
                            'id': str(transferencia.acueducto_origen.id),
                            'nombre': transferencia.acueducto_origen.nombre,
                            'codigo': transferencia.acueducto_origen.codigo
                        }
                    },
                    'destino': {
                        'hidrologica': {
                            'id': str(transferencia.hidrologica_destino.id),
                            'nombre': transferencia.hidrologica_destino.nombre,
                            'codigo': transferencia.hidrologica_destino.codigo
                        },
                        'acueducto': {
                            'id': str(transferencia.acueducto_destino.id),
                            'nombre': transferencia.acueducto_destino.nombre,
                            'codigo': transferencia.acueducto_destino.codigo
                        }
                    },
                    
                    # Fechas importantes
                    'fecha_solicitud': transferencia.fecha_solicitud.isoformat(),
                    'fecha_aprobacion': transferencia.fecha_aprobacion.isoformat() if transferencia.fecha_aprobacion else None,
                    'fecha_inicio_transito': transferencia.fecha_inicio_transito.isoformat() if transferencia.fecha_inicio_transito else None,
                    'fecha_completada': transferencia.fecha_completada.isoformat() if transferencia.fecha_completada else None,
                    
                    # Usuarios
                    'solicitado_por': {
                        'username': transferencia.solicitado_por.username,
                        'nombre_completo': transferencia.solicitado_por.get_full_name()
                    },
                    'aprobado_por': {
                        'username': transferencia.aprobado_por.username,
                        'nombre_completo': transferencia.aprobado_por.get_full_name()
                    } if transferencia.aprobado_por else None,
                    
                    # Información adicional
                    'motivo': transferencia.motivo,
                    'observaciones': transferencia.observaciones,
                    
                    # Estados posibles
                    'puede_iniciar_transito': transferencia.puede_iniciarse,
                    'puede_completar': transferencia.puede_completarse,
                    
                    # Firmas digitales
                    'firma_origen': transferencia.firma_origen,
                    'firma_destino': transferencia.firma_destino,
                    
                    # Ítems de la transferencia
                    'items': [
                        {
                            'id': str(item.item.id),
                            'sku': item.item.sku,
                            'nombre': item.item.nombre,
                            'tipo': item.item.tipo,
                            'tipo_display': item.item.get_tipo_display(),
                            'cantidad': item.cantidad,
                            'observaciones': item.observaciones,
                            'estado_actual': item.item.estado,
                            'estado_display': item.item.get_estado_display()
                        } for item in transferencia.items_transferencia.all()
                    ]
                }
            }
            
        except Exception as e:
            return {
                'valido': False,
                'error': f'Error interno: {str(e)}',
                'codigo_error': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def _extraer_parametros_url(url):
        """
        Extraer parámetros de una URL firmada
        
        Args:
            url: URL completa
        
        Returns:
            dict: Parámetros extraídos o None
        """
        try:
            from urllib.parse import urlparse, parse_qs
            
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            
            return {
                'token': params.get('token', [None])[0],
                'signature': params.get('sig', [None])[0],
                'timestamp': params.get('ts', [None])[0],
                'transferencia_id': params.get('id', [None])[0]
            }
        except Exception:
            return None
    
    @staticmethod
    def generar_qr_para_transferencia(transferencia_id):
        """
        Generar código QR completo para una transferencia
        
        Args:
            transferencia_id: ID de la transferencia
        
        Returns:
            dict: Información del QR generado
        """
        try:
            transferencia = TransferenciaExterna.objects.get(id=transferencia_id)
        except TransferenciaExterna.DoesNotExist:
            raise ValidationError("Transferencia no encontrada")
        
        # Generar token si no existe
        if not transferencia.qr_token:
            token = QRService.generar_token_seguro()
            transferencia.qr_token = token
        else:
            token = transferencia.qr_token
        
        # Crear URL firmada
        url_firmada = QRService.crear_url_firmada(str(transferencia.id), token)
        transferencia.url_firmada = url_firmada
        transferencia.save()
        
        # Generar imagen QR
        qr_buffer = QRService.generar_codigo_qr(url_firmada)
        
        return {
            'token': token,
            'url_firmada': url_firmada,
            'qr_image_buffer': qr_buffer,
            'transferencia_id': str(transferencia.id),
            'numero_orden': transferencia.numero_orden
        }
    
    @staticmethod
    def confirmar_accion_qr(token, accion, usuario, observaciones=""):
        """
        Confirmar una acción (salida/recepción) via QR
        
        Args:
            token: Token del QR
            accion: 'iniciar_transito' o 'completar'
            usuario: Usuario que confirma
            observaciones: Observaciones adicionales
        
        Returns:
            dict: Resultado de la confirmación
        """
        # Validar token
        validacion = QRService.validar_qr_token(token)
        if not validacion['valido']:
            return validacion
        
        transferencia_data = validacion['transferencia']
        
        try:
            transferencia = TransferenciaExterna.objects.get(id=transferencia_data['id'])
        except TransferenciaExterna.DoesNotExist:
            return {
                'valido': False,
                'error': 'Transferencia no encontrada',
                'codigo_error': 'TRANSFER_NOT_FOUND'
            }
        
        try:
            if accion == 'iniciar_transito':
                # Validar que el usuario pertenezca a la hidrológica origen
                if usuario.hidrologica != transferencia.hidrologica_origen:
                    return {
                        'valido': False,
                        'error': 'Usuario no autorizado para confirmar salida',
                        'codigo_error': 'UNAUTHORIZED_ORIGIN'
                    }
                
                if not transferencia.puede_iniciarse:
                    return {
                        'valido': False,
                        'error': 'La transferencia no puede iniciarse en su estado actual',
                        'codigo_error': 'INVALID_STATE_FOR_TRANSIT'
                    }
                
                # Iniciar tránsito
                from .services import TransferService
                TransferService.iniciar_transito(transferencia.id, usuario)
                
                return {
                    'valido': True,
                    'accion': 'transito_iniciado',
                    'mensaje': 'Tránsito iniciado exitosamente',
                    'estado_nuevo': 'en_transito'
                }
                
            elif accion == 'completar':
                # Validar que el usuario pertenezca a la hidrológica destino
                if usuario.hidrologica != transferencia.hidrologica_destino:
                    return {
                        'valido': False,
                        'error': 'Usuario no autorizado para confirmar recepción',
                        'codigo_error': 'UNAUTHORIZED_DESTINATION'
                    }
                
                if not transferencia.puede_completarse:
                    return {
                        'valido': False,
                        'error': 'La transferencia no puede completarse en su estado actual',
                        'codigo_error': 'INVALID_STATE_FOR_COMPLETION'
                    }
                
                # Completar transferencia
                from .services import TransferService
                TransferService.completar_transferencia(transferencia.id, usuario)
                
                return {
                    'valido': True,
                    'accion': 'transferencia_completada',
                    'mensaje': 'Transferencia completada exitosamente',
                    'estado_nuevo': 'completada'
                }
            
            else:
                return {
                    'valido': False,
                    'error': 'Acción no válida',
                    'codigo_error': 'INVALID_ACTION'
                }
                
        except ValidationError as e:
            return {
                'valido': False,
                'error': str(e),
                'codigo_error': 'BUSINESS_RULE_VIOLATION'
            }
        except Exception as e:
            return {
                'valido': False,
                'error': f'Error interno: {str(e)}',
                'codigo_error': 'INTERNAL_ERROR'
            }