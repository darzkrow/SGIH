"""
Servicios de negocio para gestión de transferencias
"""
import uuid
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import TransferenciaExterna, ItemTransferencia, MovimientoInterno, EstadoTransferencia
from apps.inventory.models import ItemInventario, EstadoItem
from apps.core.models import Hidrologica, Acueducto
from apps.core.exceptions import (
    BusinessLogicError, NotFoundError, ValidationError, StateError,
    ErrorCode
)

User = get_user_model()


class TransferService:
    """
    Servicio para gestión de transferencias externas
    """
    
    @staticmethod
    @transaction.atomic
    def solicitar_transferencia(hidrologica_origen_id, acueducto_origen_id,
                              hidrologica_destino_id, acueducto_destino_id,
                              items_solicitados, usuario, motivo, prioridad='media'):
        """
        Crear una nueva solicitud de transferencia externa
        
        Args:
            hidrologica_origen_id: ID de la hidrológica origen
            acueducto_origen_id: ID del acueducto origen
            hidrologica_destino_id: ID de la hidrológica destino
            acueducto_destino_id: ID del acueducto destino
            items_solicitados: Lista de dicts con {'item_id': str, 'cantidad': int}
            usuario: Usuario que solicita
            motivo: Motivo de la transferencia
            prioridad: Prioridad de la transferencia
        
        Returns:
            TransferenciaExterna: La transferencia creada
        """
        # Validar hidrológicas
        try:
            hidrologica_origen = Hidrologica.objects.get(id=hidrologica_origen_id)
            hidrologica_destino = Hidrologica.objects.get(id=hidrologica_destino_id)
            acueducto_origen = Acueducto.objects.get(id=acueducto_origen_id)
            acueducto_destino = Acueducto.objects.get(id=acueducto_destino_id)
        except Hidrologica.DoesNotExist:
            raise NotFoundError(
                ErrorCode.HIDROLOGICA_NOT_FOUND,
                "Hidrológica no encontrada"
            )
        except Acueducto.DoesNotExist:
            raise NotFoundError(
                ErrorCode.ACUEDUCTO_NOT_FOUND,
                "Acueducto no encontrado"
            )
        
        # Validar que no sea la misma hidrológica
        if hidrologica_origen == hidrologica_destino:
            raise ValidationError("No se puede crear transferencia externa a la misma hidrológica")
        
        # Validar que el usuario pertenezca a la hidrológica origen
        if usuario.hidrologica != hidrologica_origen:
            raise ValidationError("El usuario debe pertenecer a la hidrológica origen")
        
        # Crear la transferencia
        transferencia = TransferenciaExterna.objects.create(
            hidrologica_origen=hidrologica_origen,
            acueducto_origen=acueducto_origen,
            hidrologica_destino=hidrologica_destino,
            acueducto_destino=acueducto_destino,
            solicitado_por=usuario,
            motivo=motivo,
            prioridad=prioridad
        )
        
        # Agregar ítems a la transferencia
        for item_data in items_solicitados:
            try:
                item = ItemInventario.objects.get(id=item_data['item_id'])
                
                # Validar que el ítem pertenezca a la hidrológica origen
                if item.hidrologica != hidrologica_origen:
                    raise ValidationError(f"El ítem {item.sku} no pertenece a la hidrológica origen")
                
                # Validar que el ítem esté disponible para transferencia
                if not item.puede_transferirse:
                    raise ValidationError(f"El ítem {item.sku} no está disponible para transferencia")
                
                ItemTransferencia.objects.create(
                    transferencia=transferencia,
                    item=item,
                    cantidad=item_data.get('cantidad', 1),
                    observaciones=item_data.get('observaciones', '')
                )
                
                # Cambiar estado del ítem a "en tránsito" (se hará cuando se apruebe)
                
            except ItemInventario.DoesNotExist:
                raise ValidationError(f"Ítem con ID {item_data['item_id']} no encontrado")
        
        # Notificar al Ente Rector
        from apps.notifications.services import notificar_nueva_solicitud_transferencia
        notificar_nueva_solicitud_transferencia(transferencia)
        
        return transferencia
    
    @staticmethod
    @transaction.atomic
    def aprobar_transferencia(transferencia_id, usuario_rector, observaciones=""):
        """
        Aprobar una transferencia externa
        
        Args:
            transferencia_id: ID de la transferencia
            usuario_rector: Usuario del Ente Rector que aprueba
            observaciones: Observaciones de la aprobación
        
        Returns:
            TransferenciaExterna: La transferencia aprobada
        """
        try:
            transferencia = TransferenciaExterna.objects.get(id=transferencia_id)
        except TransferenciaExterna.DoesNotExist:
            raise ValidationError("Transferencia no encontrada")
        
        # Validar que el usuario sea del Ente Rector
        if not usuario_rector.is_ente_rector:
            raise ValidationError("Solo el Ente Rector puede aprobar transferencias")
        
        # Validar estado actual
        if transferencia.estado != EstadoTransferencia.SOLICITADA:
            raise ValidationError("Solo se pueden aprobar transferencias en estado 'solicitada'")
        
        # Aprobar la transferencia
        transferencia.aprobar(usuario_rector)
        
        if observaciones:
            transferencia.observaciones += f"\n\nAprobación: {observaciones}"
            transferencia.save()
        
        # Cambiar estado de los ítems a "en tránsito"
        for item_transferencia in transferencia.items_transferencia.all():
            item = item_transferencia.item
            item.cambiar_estado(
                EstadoItem.EN_TRANSITO,
                usuario=usuario_rector,
                observaciones=f"Transferencia aprobada - Orden {transferencia.numero_orden}"
            )
        
        # Generar orden de traspaso (tarea asíncrona)
        from .tasks import generar_orden_traspaso
        generar_orden_traspaso.delay(transferencia.id)
        
        # Notificar aprobación
        from apps.notifications.services import notificar_transferencia_aprobada
        notificar_transferencia_aprobada(transferencia)
        
        return transferencia
    
    @staticmethod
    @transaction.atomic
    def rechazar_transferencia(transferencia_id, usuario_rector, motivo_rechazo):
        """
        Rechazar una transferencia externa
        
        Args:
            transferencia_id: ID de la transferencia
            usuario_rector: Usuario del Ente Rector que rechaza
            motivo_rechazo: Motivo del rechazo
        
        Returns:
            TransferenciaExterna: La transferencia rechazada
        """
        try:
            transferencia = TransferenciaExterna.objects.get(id=transferencia_id)
        except TransferenciaExterna.DoesNotExist:
            raise ValidationError("Transferencia no encontrada")
        
        # Validar que el usuario sea del Ente Rector
        if not usuario_rector.is_ente_rector:
            raise ValidationError("Solo el Ente Rector puede rechazar transferencias")
        
        # Rechazar la transferencia
        transferencia.rechazar(usuario_rector, motivo_rechazo)
        
        # Notificar rechazo
        from apps.notifications.services import notificar_transferencia_rechazada
        notificar_transferencia_rechazada(transferencia, motivo_rechazo)
        
        return transferencia
    
    @staticmethod
    @transaction.atomic
    def iniciar_transito(transferencia_id, usuario):
        """
        Marcar transferencia como en tránsito y firmar salida
        
        Args:
            transferencia_id: ID de la transferencia
            usuario: Usuario que confirma la salida
        
        Returns:
            TransferenciaExterna: La transferencia en tránsito
        """
        try:
            transferencia = TransferenciaExterna.objects.get(id=transferencia_id)
        except TransferenciaExterna.DoesNotExist:
            raise ValidationError("Transferencia no encontrada")
        
        # Validar que el usuario pertenezca a la hidrológica origen
        if usuario.hidrologica != transferencia.hidrologica_origen:
            raise ValidationError("Solo usuarios de la hidrológica origen pueden confirmar la salida")
        
        # Iniciar tránsito
        transferencia.iniciar_transito(usuario)
        
        # Notificar que está en tránsito
        from apps.notifications.services import notificar_transferencia_en_transito
        notificar_transferencia_en_transito(transferencia)
        
        return transferencia
    
    @staticmethod
    @transaction.atomic
    def completar_transferencia(transferencia_id, usuario):
        """
        Completar transferencia y firmar recepción
        
        Args:
            transferencia_id: ID de la transferencia
            usuario: Usuario que confirma la recepción
        
        Returns:
            TransferenciaExterna: La transferencia completada
        """
        try:
            transferencia = TransferenciaExterna.objects.get(id=transferencia_id)
        except TransferenciaExterna.DoesNotExist:
            raise ValidationError("Transferencia no encontrada")
        
        # Validar que el usuario pertenezca a la hidrológica destino
        if usuario.hidrologica != transferencia.hidrologica_destino:
            raise ValidationError("Solo usuarios de la hidrológica destino pueden confirmar la recepción")
        
        # Completar transferencia
        transferencia.completar(usuario)
        
        # Actualizar ubicación de los ítems y cambiar estado
        for item_transferencia in transferencia.items_transferencia.all():
            item = item_transferencia.item
            
            # Cambiar hidrológica y acueducto
            item.hidrologica = transferencia.hidrologica_destino
            item.acueducto_actual = transferencia.acueducto_destino
            item.save()
            
            # Cambiar estado a disponible
            item.cambiar_estado(
                EstadoItem.DISPONIBLE,
                usuario=usuario,
                observaciones=f"Transferencia completada - Orden {transferencia.numero_orden}"
            )
            
            # Registrar movimiento en historial usando el nuevo servicio
            from apps.inventory.services import ItemHistoryService
            ItemHistoryService.registrar_transferencia_externa(
                item=item,
                hidrologica_origen=transferencia.hidrologica_origen,
                hidrologica_destino=transferencia.hidrologica_destino,
                acueducto_origen=transferencia.acueducto_origen,
                acueducto_destino=transferencia.acueducto_destino,
                numero_orden=transferencia.numero_orden,
                usuario=usuario,
                observaciones=f"Orden {transferencia.numero_orden} - {transferencia.motivo}"
            )
        
        # Notificar transferencia completada
        from apps.notifications.services import notificar_transferencia_completada
        notificar_transferencia_completada(transferencia)
        
        return transferencia
    
    @staticmethod
    def buscar_stock_disponible(tipo_item, hidrologica_excluir=None):
        """
        Buscar stock disponible de un tipo de ítem en todas las hidrológicas
        
        Args:
            tipo_item: Tipo de ítem a buscar
            hidrologica_excluir: Hidrológica a excluir de la búsqueda
        
        Returns:
            dict: Diccionario con hidrológicas y su stock disponible
        """
        queryset = ItemInventario.objects.filter(
            tipo=tipo_item,
            estado=EstadoItem.DISPONIBLE
        )
        
        if hidrologica_excluir:
            queryset = queryset.exclude(hidrologica=hidrologica_excluir)
        
        # Agrupar por hidrológica
        stock_por_hidrologica = {}
        for item in queryset:
            hidrologica_id = str(item.hidrologica.id)
            if hidrologica_id not in stock_por_hidrologica:
                stock_por_hidrologica[hidrologica_id] = {
                    'hidrologica': {
                        'id': hidrologica_id,
                        'nombre': item.hidrologica.nombre,
                        'codigo': item.hidrologica.codigo
                    },
                    'items': []
                }
            
            stock_por_hidrologica[hidrologica_id]['items'].append({
                'id': str(item.id),
                'sku': item.sku,
                'nombre': item.nombre,
                'acueducto': item.acueducto_actual.nombre,
                'valor_unitario': float(item.valor_unitario) if item.valor_unitario else None
            })
        
        return stock_por_hidrologica
    
    @staticmethod
    def obtener_transferencias_pendientes():
        """
        Obtener todas las transferencias pendientes de aprobación
        Solo para uso del Ente Rector
        
        Returns:
            QuerySet: Transferencias pendientes
        """
        return TransferenciaExterna.objects.filter(
            estado=EstadoTransferencia.SOLICITADA
        ).order_by('-fecha_solicitud')
    
    @staticmethod
    def obtener_transferencias_hidrologica(hidrologica_id):
        """
        Obtener transferencias que involucran una hidrológica específica
        
        Args:
            hidrologica_id: ID de la hidrológica
        
        Returns:
            QuerySet: Transferencias de la hidrológica
        """
        return TransferenciaExterna.objects.filter(
            models.Q(hidrologica_origen_id=hidrologica_id) |
            models.Q(hidrologica_destino_id=hidrologica_id)
        ).order_by('-fecha_solicitud')


class MovimientoInternoService:
    """
    Servicio para gestión de movimientos internos
    """
    
    @staticmethod
    @transaction.atomic
    def crear_movimiento_interno(item_id, acueducto_destino_id, usuario, motivo, observaciones=""):
        """
        Crear un movimiento interno dentro de la misma hidrológica
        
        Args:
            item_id: ID del ítem a mover
            acueducto_destino_id: ID del acueducto destino
            usuario: Usuario que realiza el movimiento
            motivo: Motivo del movimiento
            observaciones: Observaciones adicionales
        
        Returns:
            MovimientoInterno: El movimiento creado
        """
        try:
            item = ItemInventario.objects.get(id=item_id)
            acueducto_destino = Acueducto.objects.get(id=acueducto_destino_id)
        except (ItemInventario.DoesNotExist, Acueducto.DoesNotExist) as e:
            raise ValidationError(f"Entidad no encontrada: {e}")
        
        # Validar que el usuario pertenezca a la hidrológica del ítem
        if usuario.hidrologica != item.hidrologica:
            raise ValidationError("El usuario debe pertenecer a la misma hidrológica del ítem")
        
        # Validar que el acueducto destino pertenezca a la misma hidrológica
        if acueducto_destino.hidrologica != item.hidrologica:
            raise ValidationError("El acueducto destino debe pertenecer a la misma hidrológica")
        
        # Validar que no sea el mismo acueducto
        if item.acueducto_actual == acueducto_destino:
            raise ValidationError("El ítem ya está en el acueducto destino")
        
        # Validar que el ítem esté disponible
        if item.estado != EstadoItem.DISPONIBLE:
            raise ValidationError("Solo se pueden mover ítems en estado disponible")
        
        # Crear el movimiento
        movimiento = MovimientoInterno.objects.create(
            item=item,
            acueducto_origen=item.acueducto_actual,
            acueducto_destino=acueducto_destino,
            usuario=usuario,
            motivo=motivo,
            observaciones=observaciones
        )
        
        # Notificar movimiento interno
        from apps.notifications.services import notificar_movimiento_interno
        notificar_movimiento_interno(movimiento)
        
        return movimiento
    
    @staticmethod
    def obtener_movimientos_hidrologica(hidrologica_id, fecha_desde=None, fecha_hasta=None):
        """
        Obtener movimientos internos de una hidrológica
        
        Args:
            hidrologica_id: ID de la hidrológica
            fecha_desde: Fecha desde (opcional)
            fecha_hasta: Fecha hasta (opcional)
        
        Returns:
            QuerySet: Movimientos internos
        """
        queryset = MovimientoInterno.objects.filter(
            acueducto_origen__hidrologica_id=hidrologica_id
        )
        
        if fecha_desde:
            queryset = queryset.filter(fecha_movimiento__gte=fecha_desde)
        
        if fecha_hasta:
            queryset = queryset.filter(fecha_movimiento__lte=fecha_hasta)
        
        return queryset.order_by('-fecha_movimiento')
    
    @staticmethod
    def obtener_historial_item(item_id):
        """
        Obtener historial completo de movimientos de un ítem
        
        Args:
            item_id: ID del ítem
        
        Returns:
            dict: Historial completo del ítem
        """
        try:
            item = ItemInventario.objects.get(id=item_id)
        except ItemInventario.DoesNotExist:
            raise ValidationError("Ítem no encontrado")
        
        # Obtener movimientos internos
        movimientos_internos = MovimientoInterno.objects.filter(
            item=item
        ).order_by('fecha_movimiento')
        
        # Obtener transferencias externas
        transferencias = TransferenciaExterna.objects.filter(
            items_transferencia__item=item
        ).order_by('fecha_solicitud')
        
        return {
            'item': {
                'id': str(item.id),
                'sku': item.sku,
                'nombre': item.nombre,
                'ubicacion_actual': item.ubicacion_actual
            },
            'ficha_vida': item.historial_movimientos,
            'movimientos_internos': [
                {
                    'id': str(mov.id),
                    'fecha': mov.fecha_movimiento,
                    'origen': mov.acueducto_origen.nombre,
                    'destino': mov.acueducto_destino.nombre,
                    'usuario': mov.usuario.username,
                    'motivo': mov.motivo
                } for mov in movimientos_internos
            ],
            'transferencias_externas': [
                {
                    'id': str(trans.id),
                    'numero_orden': trans.numero_orden,
                    'fecha': trans.fecha_solicitud,
                    'estado': trans.estado,
                    'origen': trans.hidrologica_origen.nombre,
                    'destino': trans.hidrologica_destino.nombre
                } for trans in transferencias
            ]
        }