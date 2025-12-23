"""
Comando para crear usuarios de prueba del sistema
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.core.models import EnteRector, Hidrologica

User = get_user_model()


class Command(BaseCommand):
    help = 'Crear usuarios de prueba para el sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar recreación de usuarios existentes'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Contraseña para todos los usuarios de prueba'
        )
    
    def handle(self, *args, **options):
        force = options.get('force', False)
        password = options.get('password', 'admin123')
        
        try:
            with transaction.atomic():
                self.crear_usuarios_prueba(force, password)
                
                self.stdout.write(
                    self.style.SUCCESS('Usuarios de prueba creados exitosamente')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creando usuarios de prueba: {e}')
            )
    
    def crear_usuarios_prueba(self, force=False, password='admin123'):
        """Crear usuarios de prueba para diferentes roles"""
        
        # Verificar que existan las entidades necesarias
        ente_rector = EnteRector.objects.first()
        if not ente_rector:
            self.stdout.write(
                self.style.ERROR('Debe ejecutar setup_initial_data primero')
            )
            return
        
        hidrologicas = list(Hidrologica.objects.all()[:5])  # Primeras 5 hidrológicas
        if not hidrologicas:
            self.stdout.write(
                self.style.ERROR('Debe ejecutar setup_initial_data primero')
            )
            return
        
        usuarios_data = [
            # Administradores del Ente Rector
            {
                'username': 'admin_rector',
                'email': 'admin@enterector.gov.co',
                'first_name': 'Administrador',
                'last_name': 'Ente Rector',
                'rol': User.RolChoices.ADMIN_RECTOR,
                'hidrologica': None,
                'is_staff': True,
                'is_superuser': True
            },
            {
                'username': 'supervisor_rector',
                'email': 'supervisor@enterector.gov.co',
                'first_name': 'Supervisor',
                'last_name': 'Nacional',
                'rol': User.RolChoices.ADMIN_RECTOR,
                'hidrologica': None,
                'is_staff': True,
                'is_superuser': False
            },
            
            # Operadores de Hidrológicas
            {
                'username': 'operador_atlantico',
                'email': 'operador@hat.gov.co',
                'first_name': 'Operador',
                'last_name': 'Atlántico',
                'rol': User.RolChoices.OPERADOR_HIDROLOGICA,
                'hidrologica': hidrologicas[0] if len(hidrologicas) > 0 else None,
                'is_staff': False,
                'is_superuser': False
            },
            {
                'username': 'operador_bolivar',
                'email': 'operador@hbl.gov.co',
                'first_name': 'Operador',
                'last_name': 'Bolívar',
                'rol': User.RolChoices.OPERADOR_HIDROLOGICA,
                'hidrologica': hidrologicas[1] if len(hidrologicas) > 1 else None,
                'is_staff': False,
                'is_superuser': False
            },
            {
                'username': 'operador_magdalena',
                'email': 'operador@hmg.gov.co',
                'first_name': 'Operador',
                'last_name': 'Magdalena',
                'rol': User.RolChoices.OPERADOR_HIDROLOGICA,
                'hidrologica': hidrologicas[2] if len(hidrologicas) > 2 else None,
                'is_staff': False,
                'is_superuser': False
            },
            
            # Puntos de Control
            {
                'username': 'control_barranquilla',
                'email': 'control@amb.com',
                'first_name': 'Control',
                'last_name': 'Barranquilla',
                'rol': User.RolChoices.PUNTO_CONTROL,
                'hidrologica': hidrologicas[0] if len(hidrologicas) > 0 else None,
                'is_staff': False,
                'is_superuser': False
            },
            {
                'username': 'control_cartagena',
                'email': 'control@acc.com',
                'first_name': 'Control',
                'last_name': 'Cartagena',
                'rol': User.RolChoices.PUNTO_CONTROL,
                'hidrologica': hidrologicas[1] if len(hidrologicas) > 1 else None,
                'is_staff': False,
                'is_superuser': False
            },
            
            # Usuarios adicionales para pruebas
            {
                'username': 'jefe_antioquia',
                'email': 'jefe@han.gov.co',
                'first_name': 'Jefe',
                'last_name': 'Operaciones Antioquia',
                'rol': User.RolChoices.OPERADOR_HIDROLOGICA,
                'hidrologica': hidrologicas[3] if len(hidrologicas) > 3 else None,
                'is_staff': False,
                'is_superuser': False
            },
            {
                'username': 'tecnico_cundinamarca',
                'email': 'tecnico@hcu.gov.co',
                'first_name': 'Técnico',
                'last_name': 'Cundinamarca',
                'rol': User.RolChoices.PUNTO_CONTROL,
                'hidrologica': hidrologicas[4] if len(hidrologicas) > 4 else None,
                'is_staff': False,
                'is_superuser': False
            }
        ]
        
        usuarios_creados = 0
        
        for user_data in usuarios_data:
            username = user_data['username']
            
            # Verificar si el usuario ya existe
            if User.objects.filter(username=username).exists():
                if force:
                    User.objects.filter(username=username).delete()
                    self.stdout.write(f'Usuario {username} eliminado para recrear')
                else:
                    self.stdout.write(f'Usuario {username} ya existe, omitiendo...')
                    continue
            
            # Crear usuario
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=password,
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                rol=user_data['rol'],
                hidrologica=user_data['hidrologica'],
                is_staff=user_data['is_staff'],
                is_superuser=user_data['is_superuser'],
                is_active=True
            )
            
            usuarios_creados += 1
            
            self.stdout.write(
                f'Usuario creado: {username} ({user.get_rol_display()}) - '
                f'{user.hidrologica.nombre if user.hidrologica else "Ente Rector"}'
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Total usuarios creados: {usuarios_creados}')
        )
        
        # Mostrar resumen de credenciales
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('CREDENCIALES DE ACCESO'))
        self.stdout.write('='*50)
        
        for user_data in usuarios_data:
            self.stdout.write(
                f'Usuario: {user_data["username"]} | '
                f'Contraseña: {password} | '
                f'Rol: {user_data["rol"]}'
            )
        
        self.stdout.write('='*50)
        self.stdout.write(
            self.style.WARNING(
                'IMPORTANTE: Cambie estas contraseñas en producción'
            )
        )