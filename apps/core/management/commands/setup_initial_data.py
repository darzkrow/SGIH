"""
Comando para configurar datos iniciales del sistema
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.core.models import EnteRector, Hidrologica, Acueducto
from apps.notifications.models import PlantillaNotificacion, TipoNotificacion, PrioridadNotificacion

User = get_user_model()


class Command(BaseCommand):
    help = 'Configurar datos iniciales del sistema: Ente Rector, 16 Hidrológicas y Acueductos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar recreación de datos existentes'
        )
        parser.add_argument(
            '--solo-hidrologicas',
            action='store_true',
            help='Solo crear hidrológicas y acueductos'
        )
        parser.add_argument(
            '--solo-plantillas',
            action='store_true',
            help='Solo crear plantillas de notificaciones'
        )
    
    def handle(self, *args, **options):
        force = options.get('force', False)
        solo_hidrologicas = options.get('solo_hidrologicas', False)
        solo_plantillas = options.get('solo_plantillas', False)
        
        try:
            with transaction.atomic():
                if not solo_plantillas:
                    self.crear_ente_rector(force)
                    self.crear_hidrologicas_y_acueductos(force)
                
                if not solo_hidrologicas:
                    self.crear_plantillas_notificaciones(force)
                
                self.stdout.write(
                    self.style.SUCCESS('Datos iniciales configurados exitosamente')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error configurando datos iniciales: {e}')
            )
    
    def crear_ente_rector(self, force=False):
        """Crear el Ente Rector único"""
        if EnteRector.objects.exists() and not force:
            self.stdout.write('Ente Rector ya existe, omitiendo...')
            return
        
        if force:
            EnteRector.objects.all().delete()
        
        ente_rector = EnteRector.objects.create(
            nombre="Ente Rector Nacional de Servicios Públicos",
            codigo="ERNSP",
            descripcion="Entidad reguladora nacional para la coordinación de servicios públicos de agua",
            direccion="Carrera 7 No. 32-16, Bogotá D.C.",
            telefono="+57 1 234 5678",
            email="contacto@enterector.gov.co",
            sitio_web="https://www.enterector.gov.co"
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Ente Rector creado: {ente_rector.nombre}')
        )
    
    def crear_hidrologicas_y_acueductos(self, force=False):
        """Crear las 16 hidrológicas con sus acueductos"""
        if Hidrologica.objects.exists() and not force:
            self.stdout.write('Hidrológicas ya existen, omitiendo...')
            return
        
        if force:
            Hidrologica.objects.all().delete()
        
        # Datos de las 16 hidrológicas
        hidrologicas_data = [
            {
                'nombre': 'Hidrológica del Atlántico',
                'codigo': 'HAT',
                'region': 'Caribe',
                'departamento': 'Atlántico',
                'ciudad_principal': 'Barranquilla',
                'acueductos': [
                    {'nombre': 'Acueducto Metropolitano de Barranquilla', 'codigo': 'AMB'},
                    {'nombre': 'Acueducto de Soledad', 'codigo': 'ACS'},
                    {'nombre': 'Acueducto de Malambo', 'codigo': 'ACM'}
                ]
            },
            {
                'nombre': 'Hidrológica de Bolívar',
                'codigo': 'HBL',
                'region': 'Caribe',
                'departamento': 'Bolívar',
                'ciudad_principal': 'Cartagena',
                'acueductos': [
                    {'nombre': 'Acueducto de Cartagena', 'codigo': 'ACC'},
                    {'nombre': 'Acueducto de Turbaco', 'codigo': 'ACT'},
                    {'nombre': 'Acueducto de Magangué', 'codigo': 'ACG'}
                ]
            },
            {
                'nombre': 'Hidrológica del Magdalena',
                'codigo': 'HMG',
                'region': 'Caribe',
                'departamento': 'Magdalena',
                'ciudad_principal': 'Santa Marta',
                'acueductos': [
                    {'nombre': 'Acueducto de Santa Marta', 'codigo': 'ASM'},
                    {'nombre': 'Acueducto de Ciénaga', 'codigo': 'ACI'},
                    {'nombre': 'Acueducto de Fundación', 'codigo': 'AFU'}
                ]
            },
            {
                'nombre': 'Hidrológica de La Guajira',
                'codigo': 'HGU',
                'region': 'Caribe',
                'departamento': 'La Guajira',
                'ciudad_principal': 'Riohacha',
                'acueductos': [
                    {'nombre': 'Acueducto de Riohacha', 'codigo': 'ARI'},
                    {'nombre': 'Acueducto de Maicao', 'codigo': 'AMA'},
                    {'nombre': 'Acueducto de Uribia', 'codigo': 'AUR'}
                ]
            },
            {
                'nombre': 'Hidrológica de Antioquia',
                'codigo': 'HAN',
                'region': 'Andina',
                'departamento': 'Antioquia',
                'ciudad_principal': 'Medellín',
                'acueductos': [
                    {'nombre': 'Empresas Públicas de Medellín', 'codigo': 'EPM'},
                    {'nombre': 'Acueducto de Bello', 'codigo': 'ABE'},
                    {'nombre': 'Acueducto de Envigado', 'codigo': 'AEN'},
                    {'nombre': 'Acueducto de Itagüí', 'codigo': 'AIT'}
                ]
            },
            {
                'nombre': 'Hidrológica de Cundinamarca',
                'codigo': 'HCU',
                'region': 'Andina',
                'departamento': 'Cundinamarca',
                'ciudad_principal': 'Bogotá',
                'acueductos': [
                    {'nombre': 'Empresa de Acueducto de Bogotá', 'codigo': 'EAB'},
                    {'nombre': 'Acueducto de Soacha', 'codigo': 'ASO'},
                    {'nombre': 'Acueducto de Chía', 'codigo': 'ACH'},
                    {'nombre': 'Acueducto de Zipaquirá', 'codigo': 'AZI'}
                ]
            },
            {
                'nombre': 'Hidrológica del Valle del Cauca',
                'codigo': 'HVC',
                'region': 'Pacífica',
                'departamento': 'Valle del Cauca',
                'ciudad_principal': 'Cali',
                'acueductos': [
                    {'nombre': 'EMCALI Cali', 'codigo': 'EMC'},
                    {'nombre': 'Acueducto de Palmira', 'codigo': 'APA'},
                    {'nombre': 'Acueducto de Buenaventura', 'codigo': 'ABU'}
                ]
            },
            {
                'nombre': 'Hidrológica de Santander',
                'codigo': 'HSA',
                'region': 'Andina',
                'departamento': 'Santander',
                'ciudad_principal': 'Bucaramanga',
                'acueductos': [
                    {'nombre': 'Acueducto Metropolitano de Bucaramanga', 'codigo': 'AMB'},
                    {'nombre': 'Acueducto de Floridablanca', 'codigo': 'AFL'},
                    {'nombre': 'Acueducto de Girón', 'codigo': 'AGI'}
                ]
            },
            {
                'nombre': 'Hidrológica del Norte de Santander',
                'codigo': 'HNS',
                'region': 'Andina',
                'departamento': 'Norte de Santander',
                'ciudad_principal': 'Cúcuta',
                'acueductos': [
                    {'nombre': 'Acueducto de Cúcuta', 'codigo': 'ACU'},
                    {'nombre': 'Acueducto de Villa del Rosario', 'codigo': 'AVR'},
                    {'nombre': 'Acueducto de Ocaña', 'codigo': 'AOC'}
                ]
            },
            {
                'nombre': 'Hidrológica del Tolima',
                'codigo': 'HTO',
                'region': 'Andina',
                'departamento': 'Tolima',
                'ciudad_principal': 'Ibagué',
                'acueductos': [
                    {'nombre': 'IBAL Ibagué', 'codigo': 'IBA'},
                    {'nombre': 'Acueducto de Espinal', 'codigo': 'AES'},
                    {'nombre': 'Acueducto de Melgar', 'codigo': 'AME'}
                ]
            },
            {
                'nombre': 'Hidrológica del Huila',
                'codigo': 'HHU',
                'region': 'Andina',
                'departamento': 'Huila',
                'ciudad_principal': 'Neiva',
                'acueductos': [
                    {'nombre': 'Acueducto de Neiva', 'codigo': 'ANE'},
                    {'nombre': 'Acueducto de Pitalito', 'codigo': 'API'},
                    {'nombre': 'Acueducto de Garzón', 'codigo': 'AGA'}
                ]
            },
            {
                'nombre': 'Hidrológica del Cauca',
                'codigo': 'HCA',
                'region': 'Pacífica',
                'departamento': 'Cauca',
                'ciudad_principal': 'Popayán',
                'acueductos': [
                    {'nombre': 'Acueducto de Popayán', 'codigo': 'APO'},
                    {'nombre': 'Acueducto de Santander de Quilichao', 'codigo': 'ASQ'},
                    {'nombre': 'Acueducto de Puerto Tejada', 'codigo': 'APT'}
                ]
            },
            {
                'nombre': 'Hidrológica de Nariño',
                'codigo': 'HNA',
                'region': 'Pacífica',
                'departamento': 'Nariño',
                'ciudad_principal': 'Pasto',
                'acueductos': [
                    {'nombre': 'EMPOPASTO Pasto', 'codigo': 'EMP'},
                    {'nombre': 'Acueducto de Ipiales', 'codigo': 'AIP'},
                    {'nombre': 'Acueducto de Tumaco', 'codigo': 'ATU'}
                ]
            },
            {
                'nombre': 'Hidrológica del Meta',
                'codigo': 'HME',
                'region': 'Orinoquía',
                'departamento': 'Meta',
                'ciudad_principal': 'Villavicencio',
                'acueductos': [
                    {'nombre': 'EAAAY Villavicencio', 'codigo': 'EAA'},
                    {'nombre': 'Acueducto de Acacías', 'codigo': 'AAC'},
                    {'nombre': 'Acueducto de Granada', 'codigo': 'AGR'}
                ]
            },
            {
                'nombre': 'Hidrológica del Casanare',
                'codigo': 'HCS',
                'region': 'Orinoquía',
                'departamento': 'Casanare',
                'ciudad_principal': 'Yopal',
                'acueductos': [
                    {'nombre': 'Acueducto de Yopal', 'codigo': 'AYO'},
                    {'nombre': 'Acueducto de Aguazul', 'codigo': 'AAG'},
                    {'nombre': 'Acueducto de Villanueva', 'codigo': 'AVI'}
                ]
            },
            {
                'nombre': 'Hidrológica del Amazonas',
                'codigo': 'HAM',
                'region': 'Amazonía',
                'departamento': 'Amazonas',
                'ciudad_principal': 'Leticia',
                'acueductos': [
                    {'nombre': 'Acueducto de Leticia', 'codigo': 'ALE'},
                    {'nombre': 'Acueducto de Puerto Nariño', 'codigo': 'APN'},
                    {'nombre': 'Acueducto de La Chorrera', 'codigo': 'ACO'}
                ]
            }
        ]
        
        ente_rector = EnteRector.objects.first()
        if not ente_rector:
            self.stdout.write(
                self.style.ERROR('Debe crear el Ente Rector primero')
            )
            return
        
        hidrologicas_creadas = 0
        acueductos_creados = 0
        
        for hidro_data in hidrologicas_data:
            # Crear hidrológica
            hidrologica = Hidrologica.objects.create(
                ente_rector=ente_rector,
                nombre=hidro_data['nombre'],
                codigo=hidro_data['codigo'],
                region=hidro_data['region'],
                departamento=hidro_data['departamento'],
                ciudad_principal=hidro_data['ciudad_principal'],
                direccion=f"Sede principal {hidro_data['ciudad_principal']}",
                telefono=f"+57 {hidrologicas_creadas + 1} 234 5678",
                email=f"contacto@{hidro_data['codigo'].lower()}.gov.co",
                activa=True
            )
            
            hidrologicas_creadas += 1
            
            # Crear acueductos para esta hidrológica
            for acue_data in hidro_data['acueductos']:
                acueducto = Acueducto.objects.create(
                    hidrologica=hidrologica,
                    nombre=acue_data['nombre'],
                    codigo=acue_data['codigo'],
                    direccion=f"Sede {acue_data['nombre']}",
                    telefono=f"+57 {acueductos_creados + 1} 345 6789",
                    email=f"operaciones@{acue_data['codigo'].lower()}.com",
                    activo=True
                )
                
                acueductos_creados += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Creadas {hidrologicas_creadas} hidrológicas y {acueductos_creados} acueductos'
            )
        )
    
    def crear_plantillas_notificaciones(self, force=False):
        """Crear plantillas de notificaciones"""
        if PlantillaNotificacion.objects.exists() and not force:
            self.stdout.write('Plantillas de notificaciones ya existen, omitiendo...')
            return
        
        if force:
            PlantillaNotificacion.objects.all().delete()
        
        plantillas_data = [
            {
                'tipo': TipoNotificacion.NUEVA_SOLICITUD,
                'titulo_template': 'Nueva Solicitud de Transferencia #{numero_orden}',
                'mensaje_template': 'Se ha recibido una nueva solicitud de transferencia de {hidrologica_origen} a {hidrologica_destino}. Número de orden: {numero_orden}. Requiere aprobación.',
                'prioridad_default': PrioridadNotificacion.ALTA
            },
            {
                'tipo': TipoNotificacion.TRANSFERENCIA_APROBADA,
                'titulo_template': 'Transferencia Aprobada #{numero_orden}',
                'mensaje_template': 'Su solicitud de transferencia #{numero_orden} ha sido aprobada por el Ente Rector. Puede proceder con el despacho de los materiales.',
                'prioridad_default': PrioridadNotificacion.ALTA
            },
            {
                'tipo': TipoNotificacion.TRANSFERENCIA_RECHAZADA,
                'titulo_template': 'Transferencia Rechazada #{numero_orden}',
                'mensaje_template': 'Su solicitud de transferencia #{numero_orden} ha sido rechazada. Motivo: {motivo_rechazo}',
                'prioridad_default': PrioridadNotificacion.MEDIA
            },
            {
                'tipo': TipoNotificacion.TRANSFERENCIA_EN_TRANSITO,
                'titulo_template': 'Transferencia en Tránsito #{numero_orden}',
                'mensaje_template': 'La transferencia #{numero_orden} de {hidrologica_origen} está en tránsito hacia su hidrológica. Prepárese para la recepción.',
                'prioridad_default': PrioridadNotificacion.MEDIA
            },
            {
                'tipo': TipoNotificacion.TRANSFERENCIA_COMPLETADA,
                'titulo_template': 'Transferencia Completada #{numero_orden}',
                'mensaje_template': 'La transferencia #{numero_orden} entre {hidrologica_origen} y {hidrologica_destino} ha sido completada exitosamente.',
                'prioridad_default': PrioridadNotificacion.MEDIA
            },
            {
                'tipo': TipoNotificacion.MOVIMIENTO_INTERNO,
                'titulo_template': 'Movimiento Interno Realizado',
                'mensaje_template': 'Se ha realizado un movimiento interno del ítem {item_sku} de {acueducto_origen} a {acueducto_destino}.',
                'prioridad_default': PrioridadNotificacion.BAJA
            },
            {
                'tipo': TipoNotificacion.SISTEMA,
                'titulo_template': 'Notificación del Sistema',
                'mensaje_template': 'Mensaje del sistema de gestión de inventario.',
                'prioridad_default': PrioridadNotificacion.MEDIA
            }
        ]
        
        plantillas_creadas = 0
        
        for plantilla_data in plantillas_data:
            PlantillaNotificacion.objects.create(**plantilla_data)
            plantillas_creadas += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Creadas {plantillas_creadas} plantillas de notificaciones')
        )