"""
Tareas asíncronas para transferencias
"""
from celery import shared_task
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
import uuid
import hashlib
import hmac
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors


@shared_task
def generar_orden_traspaso(transferencia_id):
    """
    Generar PDF con código QR para orden de traspaso
    
    Args:
        transferencia_id: ID de la transferencia
    
    Returns:
        str: Ruta del archivo PDF generado
    """
    from .models import TransferenciaExterna
    
    try:
        transferencia = TransferenciaExterna.objects.get(id=transferencia_id)
    except TransferenciaExterna.DoesNotExist:
        return None
    
    # Generar token único y URL firmada
    token = generar_token_seguro()
    url_firmada = crear_url_firmada(str(transferencia.id), token)
    
    # Actualizar transferencia con token y URL
    transferencia.qr_token = token
    transferencia.url_firmada = url_firmada
    transferencia.save()
    
    # Generar código QR
    qr_buffer = generar_codigo_qr(url_firmada)
    
    # Generar PDF
    pdf_buffer = generar_pdf_orden(transferencia, qr_buffer)
    
    # Guardar PDF
    filename = f"orden_{transferencia.numero_orden}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = f"ordenes_traspaso/{filename}"
    
    # Guardar en storage
    saved_path = default_storage.save(file_path, ContentFile(pdf_buffer.getvalue()))
    
    # Actualizar transferencia
    transferencia.archivo_pdf = saved_path
    transferencia.pdf_generado = True
    transferencia.save()
    
    return saved_path


def generar_token_seguro():
    """
    Generar token seguro para QR
    
    Returns:
        str: Token único
    """
    return str(uuid.uuid4()).replace('-', '')


def crear_url_firmada(transferencia_id, token):
    """
    Crear URL firmada digitalmente para validación QR
    
    Args:
        transferencia_id: ID de la transferencia
        token: Token único
    
    Returns:
        str: URL firmada
    """
    # Datos a firmar
    timestamp = int(datetime.now().timestamp())
    data = f"{transferencia_id}:{token}:{timestamp}"
    
    # Crear firma HMAC
    secret_key = getattr(settings, 'SECRET_KEY', 'default-secret')
    signature = hmac.new(
        secret_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Construir URL
    base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    url = f"{base_url}/qr/validate?token={token}&sig={signature}&ts={timestamp}&id={transferencia_id}"
    
    return url


def generar_codigo_qr(url):
    """
    Generar código QR para la URL
    
    Args:
        url: URL a codificar
    
    Returns:
        BytesIO: Buffer con imagen QR
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Crear imagen
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir a buffer
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer


def generar_pdf_orden(transferencia, qr_buffer):
    """
    Generar PDF de orden de traspaso
    
    Args:
        transferencia: Instancia de TransferenciaExterna
        qr_buffer: Buffer con imagen QR
    
    Returns:
        BytesIO: Buffer con PDF generado
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Título
    title = Paragraph(
        f"<b>ORDEN DE TRASPASO</b><br/>No. {transferencia.numero_orden}",
        styles['Title']
    )
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Información de la transferencia
    info_data = [
        ['Fecha de Solicitud:', transferencia.fecha_solicitud.strftime('%d/%m/%Y %H:%M')],
        ['Estado:', transferencia.get_estado_display()],
        ['Prioridad:', transferencia.get_prioridad_display()],
        ['Solicitado por:', f"{transferencia.solicitado_por.get_full_name()} ({transferencia.solicitado_por.username})"],
    ]
    
    if transferencia.aprobado_por:
        info_data.append(['Aprobado por:', f"{transferencia.aprobado_por.get_full_name()} ({transferencia.aprobado_por.username})"])
        info_data.append(['Fecha de Aprobación:', transferencia.fecha_aprobacion.strftime('%d/%m/%Y %H:%M')])
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Origen y Destino
    origen_destino = Paragraph("<b>ORIGEN Y DESTINO</b>", styles['Heading2'])
    story.append(origen_destino)
    story.append(Spacer(1, 10))
    
    ubicacion_data = [
        ['ORIGEN', 'DESTINO'],
        [
            f"{transferencia.hidrologica_origen.nombre}\n{transferencia.acueducto_origen.nombre}",
            f"{transferencia.hidrologica_destino.nombre}\n{transferencia.acueducto_destino.nombre}"
        ]
    ]
    
    ubicacion_table = Table(ubicacion_data, colWidths=[3*inch, 3*inch])
    ubicacion_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(ubicacion_table)
    story.append(Spacer(1, 20))
    
    # Ítems de la transferencia
    items_title = Paragraph("<b>ÍTEMS A TRANSFERIR</b>", styles['Heading2'])
    story.append(items_title)
    story.append(Spacer(1, 10))
    
    items_data = [['SKU', 'Nombre', 'Tipo', 'Cantidad', 'Observaciones']]
    
    for item_transferencia in transferencia.items_transferencia.all():
        item = item_transferencia.item
        items_data.append([
            item.sku,
            item.nombre[:30] + '...' if len(item.nombre) > 30 else item.nombre,
            item.get_tipo_display(),
            str(item_transferencia.cantidad),
            item_transferencia.observaciones[:20] + '...' if len(item_transferencia.observaciones) > 20 else item_transferencia.observaciones
        ])
    
    items_table = Table(items_data, colWidths=[1.2*inch, 2*inch, 1*inch, 0.8*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 20))
    
    # Motivo
    motivo_title = Paragraph("<b>MOTIVO</b>", styles['Heading2'])
    story.append(motivo_title)
    story.append(Spacer(1, 10))
    
    motivo_text = Paragraph(transferencia.motivo, styles['Normal'])
    story.append(motivo_text)
    story.append(Spacer(1, 20))
    
    # Código QR
    qr_title = Paragraph("<b>CÓDIGO QR DE VALIDACIÓN</b>", styles['Heading2'])
    story.append(qr_title)
    story.append(Spacer(1, 10))
    
    # Crear imagen QR temporal
    qr_image = Image(qr_buffer, width=2*inch, height=2*inch)
    story.append(qr_image)
    story.append(Spacer(1, 10))
    
    qr_instructions = Paragraph(
        "Escanee este código QR para validar la autenticidad de la orden y confirmar recepción/salida.",
        styles['Normal']
    )
    story.append(qr_instructions)
    story.append(Spacer(1, 20))
    
    # Firmas
    firmas_title = Paragraph("<b>FIRMAS</b>", styles['Heading2'])
    story.append(firmas_title)
    story.append(Spacer(1, 20))
    
    firmas_data = [
        ['SALIDA', 'RECEPCIÓN'],
        ['', ''],
        ['', ''],
        ['Firma y Fecha', 'Firma y Fecha'],
        [f"Hidrológica: {transferencia.hidrologica_origen.nombre}", f"Hidrológica: {transferencia.hidrologica_destino.nombre}"]
    ]
    
    firmas_table = Table(firmas_data, colWidths=[3*inch, 3*inch], rowHeights=[0.3*inch, 1*inch, 0.3*inch, 0.3*inch, 0.3*inch])
    firmas_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 3), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(firmas_table)
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer


@shared_task
def validar_qr_token(token, signature, timestamp, transferencia_id):
    """
    Validar token QR y firma digital
    
    Args:
        token: Token del QR
        signature: Firma digital
        timestamp: Timestamp de la firma
        transferencia_id: ID de la transferencia
    
    Returns:
        dict: Resultado de la validación
    """
    try:
        # Verificar que el timestamp no sea muy antiguo (24 horas)
        current_time = int(datetime.now().timestamp())
        if current_time - int(timestamp) > 86400:  # 24 horas
            return {'valido': False, 'error': 'Token expirado'}
        
        # Reconstruir datos y verificar firma
        data = f"{transferencia_id}:{token}:{timestamp}"
        secret_key = getattr(settings, 'SECRET_KEY', 'default-secret')
        expected_signature = hmac.new(
            secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return {'valido': False, 'error': 'Firma inválida'}
        
        # Buscar transferencia
        from .models import TransferenciaExterna
        try:
            transferencia = TransferenciaExterna.objects.get(
                id=transferencia_id,
                qr_token=token
            )
        except TransferenciaExterna.DoesNotExist:
            return {'valido': False, 'error': 'Transferencia no encontrada'}
        
        # Retornar información de la transferencia
        return {
            'valido': True,
            'transferencia': {
                'id': str(transferencia.id),
                'numero_orden': transferencia.numero_orden,
                'estado': transferencia.estado,
                'estado_display': transferencia.get_estado_display(),
                'origen': {
                    'hidrologica': transferencia.hidrologica_origen.nombre,
                    'acueducto': transferencia.acueducto_origen.nombre
                },
                'destino': {
                    'hidrologica': transferencia.hidrologica_destino.nombre,
                    'acueducto': transferencia.acueducto_destino.nombre
                },
                'fecha_solicitud': transferencia.fecha_solicitud.isoformat(),
                'puede_iniciar_transito': transferencia.puede_iniciarse,
                'puede_completar': transferencia.puede_completarse,
                'items': [
                    {
                        'sku': item.item.sku,
                        'nombre': item.item.nombre,
                        'tipo': item.item.get_tipo_display(),
                        'cantidad': item.cantidad
                    } for item in transferencia.items_transferencia.all()
                ]
            }
        }
        
    except Exception as e:
        return {'valido': False, 'error': f'Error de validación: {str(e)}'}