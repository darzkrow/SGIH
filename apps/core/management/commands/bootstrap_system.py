"""
Comando maestro para inicializar completamente el sistema
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction


class Command(BaseCommand):
    help = 'Inicializar completamente el sistema con datos de prueba'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar recreación de todos los datos'
        )
        parser.add_argument(
            '--skip-inventory',
            action='store_true',
            help='Omitir creación de inventario de muestra'
        )
        parser.add_argument(
            '--inventory-size',
            type=int,
            default=50,
            help='Cantidad de ítems de inventario a crear (default: 50)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Contraseña para usuarios de prueba (default: admin123)'
        )
    
    def handle(self, *args, **options):
        force = options.get('force', False)
        skip_inventory = options.get('skip_inventory', False)
        inventory_size = options.get('inventory_size', 50)
        password = options.get('password', 'admin123')
        
        self.stdout.write(
            self.style.SUCCESS('=== INICIALIZANDO SISTEMA COMPLETO ===')
        )
        
        try:
            # Paso 1: Configurar datos iniciales
            self.stdout.write('\n1. Configurando datos iniciales...')
            call_command('setup_initial_data', force=force, verbosity=1)
            
            # Paso 2: Crear usuarios de prueba
            self.stdout.write('\n2. Creando usuarios de prueba...')
            call_command('create_test_users', force=force, password=password, verbosity=1)
            
            # Paso 3: Crear inventario de muestra (opcional)
            if not skip_inventory:
                self.stdout.write('\n3. Creando inventario de muestra...')
                call_command('create_sample_inventory', cantidad=inventory_size, force=force, verbosity=1)
            else:
                self.stdout.write('\n3. Omitiendo creación de inventario de muestra')
            
            # Paso 4: Ejecutar migraciones si es necesario
            self.stdout.write('\n4. Verificando migraciones...')
            call_command('migrate', verbosity=0)
            
            # Paso 5: Recopilar archivos estáticos (en desarrollo)
            self.stdout.write('\n5. Recopilando archivos estáticos...')
            try:
                call_command('collectstatic', interactive=False, verbosity=0)
            except Exception as e:
                self.stdout.write(f'Advertencia: Error recopilando estáticos: {e}')
            
            self.mostrar_resumen_final(password, inventory_size, skip_inventory)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error durante la inicialización: {e}')
            )
            raise
    
    def mostrar_resumen_final(self, password, inventory_size, skip_inventory):
        """Mostrar resumen final de la inicialización"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('SISTEMA INICIALIZADO EXITOSAMENTE'))
        self.stdout.write('='*60)
        
        # Contar entidades creadas
        from apps.core.models import EnteRector, Hidrologica, Acueducto
        from apps.inventory.models import ItemInventario
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        ente_rector_count = EnteRector.objects.count()
        hidrologicas_count = Hidrologica.objects.count()
        acueductos_count = Acueducto.objects.count()
        usuarios_count = User.objects.count()
        items_count = ItemInventario.objects.count()
        
        self.stdout.write(f'📋 Ente Rector: {ente_rector_count}')
        self.stdout.write(f'🏢 Hidrológicas: {hidrologicas_count}')
        self.stdout.write(f'🚰 Acueductos: {acueductos_count}')
        self.stdout.write(f'👥 Usuarios: {usuarios_count}')
        
        if not skip_inventory:
            self.stdout.write(f'📦 Ítems de inventario: {items_count}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('CREDENCIALES DE ACCESO'))
        self.stdout.write('='*60)
        
        credenciales = [
            ('admin_rector', 'Administrador Ente Rector', 'Acceso completo al sistema'),
            ('supervisor_rector', 'Supervisor Nacional', 'Supervisión y reportes'),
            ('operador_atlantico', 'Operador Atlántico', 'Gestión Hidrológica Atlántico'),
            ('operador_bolivar', 'Operador Bolívar', 'Gestión Hidrológica Bolívar'),
            ('control_barranquilla', 'Control Barranquilla', 'Punto de control QR'),
            ('control_cartagena', 'Control Cartagena', 'Punto de control QR')
        ]
        
        for username, descripcion, funciones in credenciales:
            self.stdout.write(f'🔑 {username} | {password} | {descripcion}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('ENDPOINTS PRINCIPALES'))
        self.stdout.write('='*60)
        
        endpoints = [
            ('Admin Django', '/admin/'),
            ('API Docs', '/api/docs/'),
            ('API Schema', '/api/schema/'),
            ('Auth API', '/api/v1/auth/'),
            ('Inventory API', '/api/v1/inventory/'),
            ('Transfers API', '/api/v1/transfers/'),
            ('Notifications API', '/api/v1/notifications/')
        ]
        
        for nombre, url in endpoints:
            self.stdout.write(f'🌐 {nombre}: {url}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('COMANDOS ÚTILES'))
        self.stdout.write('='*60)
        
        comandos = [
            ('Probar notificaciones', 'python manage.py test_notifications --usuario admin_rector'),
            ('Probar historial', 'python manage.py test_historial --crear-eventos --mostrar-reporte'),
            ('Crear más inventario', f'python manage.py create_sample_inventory --cantidad 100'),
            ('Recrear datos', 'python manage.py bootstrap_system --force'),
            ('Ver logs', 'docker-compose logs -f web')
        ]
        
        for descripcion, comando in comandos:
            self.stdout.write(f'⚡ {descripcion}:')
            self.stdout.write(f'   {comando}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.WARNING('IMPORTANTE: Cambie las contraseñas en producción')
        )
        self.stdout.write('='*60)
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 ¡Sistema listo para usar!')
        )