"""
Comando para crear inventario de muestra
"""
import random
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.core.models import Hidrologica, Acueducto
from apps.inventory.models import ItemInventario, TipoItem, EstadoItem, CategoriaItem
from apps.inventory.services import InventoryService

User = get_user_model()


class Command(BaseCommand):
    help = 'Crear inventario de muestra para pruebas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--cantidad',
            type=int,
            default=100,
            help='Cantidad de ítems a crear (default: 100)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar recreación eliminando inventario existente'
        )
    
    def handle(self, *args, **options):
        cantidad = options.get('cantidad', 100)
        force = options.get('force', False)
        
        try:
            with transaction.atomic():
                if force:
                    self.limpiar_inventario_existente()
                
                self.crear_categorias()
                self.crear_inventario_muestra(cantidad)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Inventario de muestra creado exitosamente: {cantidad} ítems')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creando inventario de muestra: {e}')
            )
    
    def limpiar_inventario_existente(self):
        """Limpiar inventario existente"""
        count = ItemInventario.objects.count()
        if count > 0:
            ItemInventario.objects.all().delete()
            self.stdout.write(f'Eliminados {count} ítems existentes')
    
    def crear_categorias(self):
        """Crear categorías de ítems si no existen"""
        categorias_data = [
            # Tuberías
            {'nombre': 'Tubería PVC', 'tipo_item': TipoItem.TUBERIA, 'descripcion': 'Tuberías de PVC para distribución'},
            {'nombre': 'Tubería Hierro', 'tipo_item': TipoItem.TUBERIA, 'descripcion': 'Tuberías de hierro fundido'},
            {'nombre': 'Tubería HDPE', 'tipo_item': TipoItem.TUBERIA, 'descripcion': 'Tuberías de polietileno de alta densidad'},
            
            # Motores
            {'nombre': 'Motor Centrífugo', 'tipo_item': TipoItem.MOTOR, 'descripcion': 'Motores centrífugos para bombeo'},
            {'nombre': 'Motor Sumergible', 'tipo_item': TipoItem.MOTOR, 'descripcion': 'Motores sumergibles para pozos'},
            {'nombre': 'Motor Turbina', 'tipo_item': TipoItem.MOTOR, 'descripcion': 'Motores tipo turbina'},
            
            # Válvulas
            {'nombre': 'Válvula Compuerta', 'tipo_item': TipoItem.VALVULA, 'descripcion': 'Válvulas de compuerta'},
            {'nombre': 'Válvula Mariposa', 'tipo_item': TipoItem.VALVULA, 'descripcion': 'Válvulas tipo mariposa'},
            {'nombre': 'Válvula Check', 'tipo_item': TipoItem.VALVULA, 'descripcion': 'Válvulas de retención'},
            
            # Químicos
            {'nombre': 'Cloro Líquido', 'tipo_item': TipoItem.QUIMICO, 'descripcion': 'Cloro para desinfección'},
            {'nombre': 'Sulfato de Aluminio', 'tipo_item': TipoItem.QUIMICO, 'descripcion': 'Coagulante para tratamiento'},
            {'nombre': 'Cal Hidratada', 'tipo_item': TipoItem.QUIMICO, 'descripcion': 'Cal para ajuste de pH'}
        ]
        
        categorias_creadas = 0
        
        for cat_data in categorias_data:
            categoria, created = CategoriaItem.objects.get_or_create(
                nombre=cat_data['nombre'],
                tipo_item=cat_data['tipo_item'],
                defaults={
                    'descripcion': cat_data['descripcion'],
                    'activa': True
                }
            )
            
            if created:
                categorias_creadas += 1
        
        if categorias_creadas > 0:
            self.stdout.write(f'Creadas {categorias_creadas} categorías')
    
    def crear_inventario_muestra(self, cantidad):
        """Crear ítems de inventario de muestra"""
        
        # Obtener datos necesarios
        hidrologicas = list(Hidrologica.objects.all())
        if not hidrologicas:
            self.stdout.write(
                self.style.ERROR('Debe ejecutar setup_initial_data primero')
            )
            return
        
        acueductos = list(Acueducto.objects.all())
        if not acueductos:
            self.stdout.write(
                self.style.ERROR('No hay acueductos disponibles')
            )
            return
        
        categorias = list(CategoriaItem.objects.all())
        usuarios = list(User.objects.filter(is_active=True))
        
        # Plantillas de ítems por tipo
        plantillas_items = {
            TipoItem.TUBERIA: [
                {'nombre': 'Tubería PVC 4"', 'descripcion': 'Tubería PVC de 4 pulgadas'},
                {'nombre': 'Tubería PVC 6"', 'descripcion': 'Tubería PVC de 6 pulgadas'},
                {'nombre': 'Tubería PVC 8"', 'descripcion': 'Tubería PVC de 8 pulgadas'},
                {'nombre': 'Tubería Hierro 6"', 'descripcion': 'Tubería hierro fundido 6 pulgadas'},
                {'nombre': 'Tubería HDPE 4"', 'descripcion': 'Tubería HDPE de 4 pulgadas'},
            ],
            TipoItem.MOTOR: [
                {'nombre': 'Motor Centrífugo 5HP', 'descripcion': 'Motor centrífugo de 5 caballos'},
                {'nombre': 'Motor Centrífugo 10HP', 'descripcion': 'Motor centrífugo de 10 caballos'},
                {'nombre': 'Motor Sumergible 3HP', 'descripcion': 'Motor sumergible de 3 caballos'},
                {'nombre': 'Motor Sumergible 7.5HP', 'descripcion': 'Motor sumergible de 7.5 caballos'},
                {'nombre': 'Motor Turbina 15HP', 'descripcion': 'Motor turbina de 15 caballos'},
            ],
            TipoItem.VALVULA: [
                {'nombre': 'Válvula Compuerta 4"', 'descripcion': 'Válvula compuerta de 4 pulgadas'},
                {'nombre': 'Válvula Compuerta 6"', 'descripcion': 'Válvula compuerta de 6 pulgadas'},
                {'nombre': 'Válvula Mariposa 8"', 'descripcion': 'Válvula mariposa de 8 pulgadas'},
                {'nombre': 'Válvula Check 4"', 'descripcion': 'Válvula check de 4 pulgadas'},
                {'nombre': 'Válvula Reguladora 6"', 'descripcion': 'Válvula reguladora de presión'},
            ],
            TipoItem.QUIMICO: [
                {'nombre': 'Cloro Líquido 50L', 'descripcion': 'Cloro líquido bidón de 50 litros'},
                {'nombre': 'Cloro Líquido 200L', 'descripcion': 'Cloro líquido bidón de 200 litros'},
                {'nombre': 'Sulfato Aluminio 25Kg', 'descripcion': 'Sulfato de aluminio saco de 25 kg'},
                {'nombre': 'Cal Hidratada 20Kg', 'descripcion': 'Cal hidratada saco de 20 kg'},
                {'nombre': 'Polímero Floculante 1Kg', 'descripcion': 'Polímero floculante de 1 kg'},
            ]
        }
        
        # Proveedores de muestra
        proveedores = [
            'Suministros Industriales S.A.S.',
            'Equipos y Materiales Ltda.',
            'Distribuidora Nacional',
            'Tecnología Hidráulica S.A.',
            'Materiales Especializados',
            'Suministros del Caribe',
            'Equipos Andinos S.A.S.',
            'Distribuciones del Valle'
        ]
        
        items_creados = 0
        
        for i in range(cantidad):
            # Seleccionar tipo de ítem aleatoriamente
            tipo = random.choice(list(TipoItem.choices))[0]
            plantilla = random.choice(plantillas_items[tipo])
            
            # Seleccionar hidrológica y acueducto
            hidrologica = random.choice(hidrologicas)
            acueductos_hidrologica = [a for a in acueductos if a.hidrologica == hidrologica]
            if not acueductos_hidrologica:
                continue
            
            acueducto = random.choice(acueductos_hidrologica)
            
            # Seleccionar categoría compatible
            categorias_tipo = [c for c in categorias if c.tipo_item == tipo]
            categoria = random.choice(categorias_tipo) if categorias_tipo else None
            
            # Generar datos del ítem
            sku = f"{tipo.upper()}-{hidrologica.codigo}-{i+1:04d}"
            nombre = plantilla['nombre']
            descripcion = plantilla['descripcion']
            
            # Estado aleatorio (mayoría disponibles)
            estados_ponderados = [
                (EstadoItem.DISPONIBLE, 70),
                (EstadoItem.ASIGNADO, 15),
                (EstadoItem.EN_TRANSITO, 5),
                (EstadoItem.MANTENIMIENTO, 8),
                (EstadoItem.DADO_BAJA, 2)
            ]
            
            estado = self.seleccionar_ponderado(estados_ponderados)
            
            # Valor unitario aleatorio
            rangos_valor = {
                TipoItem.TUBERIA: (50000, 500000),
                TipoItem.MOTOR: (1000000, 15000000),
                TipoItem.VALVULA: (200000, 2000000),
                TipoItem.QUIMICO: (30000, 200000)
            }
            
            valor_min, valor_max = rangos_valor[tipo]
            valor_unitario = Decimal(random.randint(valor_min, valor_max))
            
            # Fecha de adquisición aleatoria (último año)
            fecha_adquisicion = date.today() - timedelta(days=random.randint(1, 365))
            
            # Proveedor aleatorio
            proveedor = random.choice(proveedores)
            numero_factura = f"FAC-{random.randint(1000, 9999)}-{random.randint(2023, 2024)}"
            
            # Especificaciones técnicas aleatorias
            especificaciones = self.generar_especificaciones(tipo)
            
            # Crear ítem usando el servicio
            usuario_creador = random.choice(usuarios) if usuarios else None
            
            try:
                item = InventoryService.crear_item(
                    datos_item={
                        'sku': sku,
                        'tipo': tipo,
                        'nombre': nombre,
                        'descripcion': descripcion,
                        'estado': estado,
                        'hidrologica': hidrologica,
                        'acueducto_actual': acueducto,
                        'categoria': categoria,
                        'especificaciones': especificaciones,
                        'valor_unitario': valor_unitario,
                        'fecha_adquisicion': fecha_adquisicion,
                        'proveedor': proveedor,
                        'numero_factura': numero_factura
                    },
                    usuario=usuario_creador
                )
                
                items_creados += 1
                
                # Mostrar progreso cada 20 ítems
                if items_creados % 20 == 0:
                    self.stdout.write(f'Creados {items_creados}/{cantidad} ítems...')
                
            except Exception as e:
                self.stdout.write(f'Error creando ítem {sku}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Total ítems creados: {items_creados}')
        )
        
        # Mostrar estadísticas
        self.mostrar_estadisticas()
    
    def seleccionar_ponderado(self, opciones_ponderadas):
        """Seleccionar opción basada en pesos"""
        total_peso = sum(peso for _, peso in opciones_ponderadas)
        r = random.randint(1, total_peso)
        
        peso_acumulado = 0
        for opcion, peso in opciones_ponderadas:
            peso_acumulado += peso
            if r <= peso_acumulado:
                return opcion
        
        return opciones_ponderadas[0][0]  # Fallback
    
    def generar_especificaciones(self, tipo):
        """Generar especificaciones técnicas según el tipo"""
        especificaciones = {}
        
        if tipo == TipoItem.TUBERIA:
            especificaciones = {
                'material': random.choice(['PVC', 'Hierro Fundido', 'HDPE', 'Acero']),
                'diametro_pulgadas': random.choice([4, 6, 8, 10, 12]),
                'presion_trabajo_psi': random.choice([150, 200, 250, 300]),
                'longitud_metros': random.randint(6, 12),
                'norma': random.choice(['ASTM D2241', 'ISO 4422', 'NTC 382'])
            }
        
        elif tipo == TipoItem.MOTOR:
            especificaciones = {
                'potencia_hp': random.choice([3, 5, 7.5, 10, 15, 20]),
                'voltaje': random.choice([220, 440, 480]),
                'frecuencia_hz': 60,
                'rpm': random.choice([1750, 3500]),
                'eficiencia_porcentaje': random.randint(85, 95),
                'marca': random.choice(['WEG', 'Siemens', 'ABB', 'Baldor'])
            }
        
        elif tipo == TipoItem.VALVULA:
            especificaciones = {
                'tipo': random.choice(['Compuerta', 'Mariposa', 'Check', 'Reguladora']),
                'diametro_pulgadas': random.choice([4, 6, 8, 10]),
                'material_cuerpo': random.choice(['Hierro Fundido', 'Acero Inoxidable', 'Bronce']),
                'presion_trabajo_psi': random.choice([150, 200, 250]),
                'conexion': random.choice(['Bridada', 'Roscada', 'Soldada'])
            }
        
        elif tipo == TipoItem.QUIMICO:
            especificaciones = {
                'concentracion_porcentaje': random.randint(10, 99),
                'presentacion': random.choice(['Líquido', 'Polvo', 'Granulado']),
                'capacidad_litros': random.choice([20, 50, 100, 200]) if random.choice([True, False]) else None,
                'peso_kg': random.choice([20, 25, 50]) if random.choice([True, False]) else None,
                'ph': round(random.uniform(6.5, 8.5), 1),
                'vida_util_meses': random.randint(12, 36)
            }
        
        return especificaciones
    
    def mostrar_estadisticas(self):
        """Mostrar estadísticas del inventario creado"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('ESTADÍSTICAS DEL INVENTARIO'))
        self.stdout.write('='*50)
        
        # Por tipo
        self.stdout.write('Por tipo:')
        for tipo_choice in TipoItem.choices:
            tipo_code, tipo_name = tipo_choice
            count = ItemInventario.objects.filter(tipo=tipo_code).count()
            self.stdout.write(f'  {tipo_name}: {count}')
        
        # Por estado
        self.stdout.write('\nPor estado:')
        for estado_choice in EstadoItem.choices:
            estado_code, estado_name = estado_choice
            count = ItemInventario.objects.filter(estado=estado_code).count()
            self.stdout.write(f'  {estado_name}: {count}')
        
        # Por hidrológica
        self.stdout.write('\nPor hidrológica:')
        from django.db.models import Count
        stats = ItemInventario.objects.values(
            'hidrologica__nombre'
        ).annotate(
            total=Count('id')
        ).order_by('-total')
        
        for stat in stats[:10]:  # Top 10
            self.stdout.write(f'  {stat["hidrologica__nombre"]}: {stat["total"]}')
        
        self.stdout.write('='*50)