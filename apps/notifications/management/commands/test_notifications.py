"""
Comando para probar el sistema de notificaciones
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.notifications.services import notification_service
from apps.notifications.models import TipoNotificacion

User = get_user_model()


class Command(BaseCommand):
    help = 'Probar el sistema de notificaciones'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--usuario',
            type=str,
            help='Username del usuario para enviar notificación de prueba'
        )
        parser.add_argument(
            '--tipo',
            type=str,
            choices=[choice[0] for choice in TipoNotificacion.choices],
            default=TipoNotificacion.SISTEMA,
            help='Tipo de notificación a enviar'
        )
    
    def handle(self, *args, **options):
        usuario_username = options.get('usuario')
        tipo = options.get('tipo')
        
        if usuario_username:
            # Enviar notificación a usuario específico
            try:
                usuario = User.objects.get(username=usuario_username)
                
                notificacion = notification_service.enviar_notificacion(
                    usuario_id=usuario.id,
                    tipo=tipo,
                    titulo="Notificación de prueba",
                    mensaje="Esta es una notificación de prueba del sistema.",
                    datos_adicionales={
                        'test': True,
                        'comando': 'test_notifications'
                    }
                )
                
                if notificacion:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Notificación enviada exitosamente a {usuario.username} '
                            f'(ID: {notificacion.id})'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'No se pudo enviar la notificación a {usuario.username} '
                            f'(posiblemente por configuración de canal)'
                        )
                    )
                    
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Usuario "{usuario_username}" no encontrado')
                )
        else:
            # Mostrar estadísticas generales
            self.mostrar_estadisticas()
    
    def mostrar_estadisticas(self):
        """Mostrar estadísticas del sistema de notificaciones"""
        from apps.notifications.models import Notificacion, CanalNotificacion
        from django.db.models import Count, Q
        
        self.stdout.write(self.style.SUCCESS('=== ESTADÍSTICAS DEL SISTEMA DE NOTIFICACIONES ==='))
        
        # Total de notificaciones
        total_notificaciones = Notificacion.objects.count()
        total_leidas = Notificacion.objects.filter(leida=True).count()
        total_no_leidas = Notificacion.objects.filter(leida=False).count()
        
        self.stdout.write(f'Total de notificaciones: {total_notificaciones}')
        self.stdout.write(f'Leídas: {total_leidas}')
        self.stdout.write(f'No leídas: {total_no_leidas}')
        
        if total_notificaciones > 0:
            porcentaje_lectura = (total_leidas / total_notificaciones) * 100
            self.stdout.write(f'Porcentaje de lectura: {porcentaje_lectura:.1f}%')
        
        # Por tipo
        self.stdout.write('\n--- Por tipo ---')
        tipos_stats = Notificacion.objects.values('tipo').annotate(
            total=Count('id'),
            leidas=Count('id', filter=Q(leida=True))
        ).order_by('-total')
        
        for stat in tipos_stats:
            tipo_display = dict(TipoNotificacion.choices).get(stat['tipo'], stat['tipo'])
            self.stdout.write(
                f'{tipo_display}: {stat["total"]} total, {stat["leidas"]} leídas'
            )
        
        # Canales configurados
        total_canales = CanalNotificacion.objects.count()
        canales_activos = CanalNotificacion.objects.filter(
            email_habilitado=True
        ).count()
        
        self.stdout.write(f'\n--- Canales ---')
        self.stdout.write(f'Total de canales configurados: {total_canales}')
        self.stdout.write(f'Canales con email habilitado: {canales_activos}')
        
        # Usuarios activos
        usuarios_activos = User.objects.filter(is_active=True).count()
        self.stdout.write(f'Usuarios activos en el sistema: {usuarios_activos}')
        
        self.stdout.write(
            self.style.SUCCESS('\n=== FIN DE ESTADÍSTICAS ===')
        )