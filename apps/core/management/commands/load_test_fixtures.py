"""
Comando para cargar fixtures de testing
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction


class Command(BaseCommand):
    help = 'Cargar fixtures de testing para pruebas automatizadas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fixture',
            type=str,
            choices=['minimal', 'complete', 'test'],
            default='test',
            help='Tipo de fixture a cargar (default: test)'
        )
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Limpiar base de datos antes de cargar fixtures'
        )
    
    def handle(self, *args, **options):
        fixture_type = options.get('fixture', 'test')
        flush = options.get('flush', False)
        
        try:
            with transaction.atomic():
                if flush:
                    self.stdout.write('Limpiando base de datos...')
                    call_command('flush', interactive=False, verbosity=0)
                
                self.cargar_fixtures(fixture_type)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Fixtures de {fixture_type} cargados exitosamente')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error cargando fixtures: {e}')
            )
    
    def cargar_fixtures(self, fixture_type):
        """Cargar fixtures según el tipo"""
        
        if fixture_type == 'minimal':
            # Solo datos organizacionales básicos
            self.stdout.write('Cargando fixtures mínimos...')
            call_command('loaddata', 'fixtures/initial_data.json', verbosity=1)
            
        elif fixture_type == 'complete':
            # Datos completos del sistema
            self.stdout.write('Cargando fixtures completos...')
            call_command('setup_initial_data', verbosity=1)
            call_command('create_test_users', verbosity=1)
            
        elif fixture_type == 'test':
            # Datos específicos para testing
            self.stdout.write('Cargando fixtures de testing...')
            call_command('loaddata', 'fixtures/test_data.json', verbosity=1)
        
        self.mostrar_resumen()
    
    def mostrar_resumen(self):
        """Mostrar resumen de datos cargados"""
        from apps.core.models import EnteRector, Hidrologica, Acueducto
        from apps.inventory.models import ItemInventario, CategoriaItem
        from apps.notifications.models import PlantillaNotificacion
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        self.stdout.write('\n' + '='*40)
        self.stdout.write(self.style.SUCCESS('RESUMEN DE DATOS CARGADOS'))
        self.stdout.write('='*40)
        
        # Contar entidades
        stats = {
            'Ente Rector': EnteRector.objects.count(),
            'Hidrológicas': Hidrologica.objects.count(),
            'Acueductos': Acueducto.objects.count(),
            'Usuarios': User.objects.count(),
            'Categorías': CategoriaItem.objects.count(),
            'Ítems de Inventario': ItemInventario.objects.count(),
            'Plantillas de Notificación': PlantillaNotificacion.objects.count()
        }
        
        for entidad, count in stats.items():
            self.stdout.write(f'{entidad}: {count}')
        
        # Mostrar usuarios disponibles
        if User.objects.exists():
            self.stdout.write('\n--- Usuarios Disponibles ---')
            for user in User.objects.all()[:10]:  # Primeros 10
                hidrologica_info = f" ({user.hidrologica.codigo})" if user.hidrologica else " (Ente Rector)"
                self.stdout.write(f'- {user.username} - {user.get_rol_display()}{hidrologica_info}')
        
        # Mostrar ítems de inventario
        if ItemInventario.objects.exists():
            self.stdout.write('\n--- Ítems de Inventario ---')
            for item in ItemInventario.objects.all()[:5]:  # Primeros 5
                self.stdout.write(f'- {item.sku}: {item.nombre} ({item.hidrologica.codigo})')
        
        self.stdout.write('='*40)