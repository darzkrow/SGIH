"""
Modelos organizacionales del sistema
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class EnteRector(models.Model):
    """
    Entidad central que coordina las 16 hidrológicas
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    codigo = models.CharField(max_length=10, unique=True, verbose_name="Código")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")

    class Meta:
        verbose_name = "Ente Rector"
        verbose_name_plural = "Entes Rectores"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    def clean(self):
        """Validar que solo exista un Ente Rector activo"""
        if self.activo:
            existing = EnteRector.objects.filter(activo=True).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError("Solo puede existir un Ente Rector activo en el sistema")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Hidrologica(models.Model):
    """
    Entidad autónoma que gestiona acueductos y mantiene inventario
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ente_rector = models.ForeignKey(
        EnteRector, 
        on_delete=models.CASCADE, 
        related_name='hidrologicas',
        verbose_name="Ente Rector"
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    codigo = models.CharField(max_length=10, unique=True, verbose_name="Código")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    direccion = models.TextField(blank=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")

    class Meta:
        verbose_name = "Hidrológica"
        verbose_name_plural = "Hidrológicas"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    def clean(self):
        """Validar que no excedan las 16 hidrológicas activas"""
        if self.activa:
            existing_count = Hidrologica.objects.filter(activa=True).exclude(pk=self.pk).count()
            if existing_count >= 16:
                raise ValidationError("No se pueden tener más de 16 hidrológicas activas")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Acueducto(models.Model):
    """
    Unidad operativa dentro de una hidrológica
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hidrologica = models.ForeignKey(
        Hidrologica, 
        on_delete=models.CASCADE, 
        related_name='acueductos',
        verbose_name="Hidrológica"
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    codigo = models.CharField(max_length=20, verbose_name="Código")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    direccion = models.TextField(blank=True, verbose_name="Dirección")
    
    # Coordenadas GPS
    ubicacion = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Coordenadas GPS: {'lat': 0.0, 'lng': 0.0}",
        verbose_name="Ubicación GPS"
    )
    
    activo = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")

    class Meta:
        verbose_name = "Acueducto"
        verbose_name_plural = "Acueductos"
        ordering = ['hidrologica__nombre', 'nombre']
        unique_together = [['hidrologica', 'codigo']]

    def __str__(self):
        return f"{self.nombre} - {self.hidrologica.nombre}"

    @property
    def codigo_completo(self):
        """Código completo incluyendo hidrológica"""
        return f"{self.hidrologica.codigo}-{self.codigo}"


class User(AbstractUser):
    """
    Usuario extendido con relación a hidrológica
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hidrologica = models.ForeignKey(
        Hidrologica, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='usuarios',
        verbose_name="Hidrológica"
    )
    
    # Roles del sistema
    class RolChoices(models.TextChoices):
        ADMIN_RECTOR = 'admin_rector', 'Administrador Rector'
        OPERADOR_HIDROLOGICA = 'operador_hidrologica', 'Operador Hidrológica'
        PUNTO_CONTROL = 'punto_control', 'Punto de Control'
    
    rol = models.CharField(
        max_length=20, 
        choices=RolChoices.choices, 
        default=RolChoices.OPERADOR_HIDROLOGICA,
        verbose_name="Rol"
    )
    
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"

    @property
    def is_ente_rector(self):
        """Verifica si el usuario es administrador del ente rector"""
        return self.rol == self.RolChoices.ADMIN_RECTOR

    @property
    def is_operador_hidrologica(self):
        """Verifica si el usuario es operador de hidrológica"""
        return self.rol == self.RolChoices.OPERADOR_HIDROLOGICA

    @property
    def is_punto_control(self):
        """Verifica si el usuario es punto de control"""
        return self.rol == self.RolChoices.PUNTO_CONTROL

    def clean(self):
        """Validaciones del usuario"""
        if self.rol == self.RolChoices.OPERADOR_HIDROLOGICA and not self.hidrologica:
            raise ValidationError("Los operadores de hidrológica deben tener una hidrológica asignada")
        
        if self.rol == self.RolChoices.ADMIN_RECTOR and self.hidrologica:
            raise ValidationError("Los administradores rectores no deben tener hidrológica asignada")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)