# Configuración Inicial del Sistema

Este documento describe cómo configurar el sistema de gestión de inventario para las 16 Hidrológicas.

## Requisitos Previos

- Docker y Docker Compose instalados
- Python 3.11+ (si se ejecuta localmente)
- PostgreSQL 15+ (si se ejecuta localmente)
- Redis 7+ (si se ejecuta localmente)

## Configuración con Docker (Recomendado)

### 1. Clonar y Configurar

```bash
# Clonar el repositorio
git clone <repository-url>
cd inventory-platform

# Copiar variables de entorno
cp .env.example .env

# Editar variables según el ambiente
nano .env
```

### 2. Construir y Ejecutar

```bash
# Construir contenedores
docker-compose build

# Ejecutar migraciones
docker-compose run --rm web python manage.py migrate

# Inicializar sistema completo
docker-compose run --rm web python manage.py bootstrap_system

# Iniciar servicios
docker-compose up -d
```

### 3. Verificar Instalación

```bash
# Ver logs
docker-compose logs -f web

# Acceder al contenedor
docker-compose exec web bash

# Verificar servicios
curl http://localhost:8000/api/docs/
```

## Configuración Manual (Desarrollo)

### 1. Instalar Dependencias

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar Base de Datos

```bash
# Crear base de datos PostgreSQL
createdb inventory_db

# Configurar variables de entorno
export DB_NAME=inventory_db
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_HOST=localhost
export DB_PORT=5432
export REDIS_URL=redis://localhost:6379/0
```

### 3. Ejecutar Migraciones e Inicialización

```bash
# Ejecutar migraciones
python manage.py migrate

# Inicializar sistema completo
python manage.py bootstrap_system

# Crear superusuario adicional (opcional)
python manage.py createsuperuser
```

### 4. Iniciar Servicios

```bash
# Terminal 1: Servidor Django
python manage.py runserver

# Terminal 2: Worker Celery
celery -A inventory_platform worker -l info

# Terminal 3: Celery Beat (tareas programadas)
celery -A inventory_platform beat -l info
```

## Comandos de Inicialización

### Comando Principal

```bash
# Inicializar sistema completo
python manage.py bootstrap_system

# Opciones disponibles
python manage.py bootstrap_system --help
```

### Comandos Individuales

```bash
# 1. Crear Ente Rector y 16 Hidrológicas
python manage.py setup_initial_data

# 2. Crear usuarios de prueba
python manage.py create_test_users

# 3. Crear inventario de muestra
python manage.py create_sample_inventory --cantidad 100

# 4. Probar notificaciones
python manage.py test_notifications --usuario admin_rector

# 5. Probar historial de ítems
python manage.py test_historial --crear-eventos --mostrar-reporte
```

### Opciones de Forzado

```bash
# Recrear todos los datos
python manage.py bootstrap_system --force

# Recrear solo datos iniciales
python manage.py setup_initial_data --force

# Recrear solo usuarios
python manage.py create_test_users --force

# Recrear solo inventario
python manage.py create_sample_inventory --force
```

## Datos Iniciales Creados

### Ente Rector
- **Nombre**: Ente Rector Nacional de Servicios Públicos
- **Código**: ERNSP

### 16 Hidrológicas por Región

#### Región Caribe
1. **Hidrológica del Atlántico (HAT)** - Barranquilla
2. **Hidrológica de Bolívar (HBL)** - Cartagena
3. **Hidrológica del Magdalena (HMG)** - Santa Marta
4. **Hidrológica de La Guajira (HGU)** - Riohacha

#### Región Andina
5. **Hidrológica de Antioquia (HAN)** - Medellín
6. **Hidrológica de Cundinamarca (HCU)** - Bogotá
7. **Hidrológica de Santander (HSA)** - Bucaramanga
8. **Hidrológica del Norte de Santander (HNS)** - Cúcuta
9. **Hidrológica del Tolima (HTO)** - Ibagué
10. **Hidrológica del Huila (HHU)** - Neiva

#### Región Pacífica
11. **Hidrológica del Valle del Cauca (HVC)** - Cali
12. **Hidrológica del Cauca (HCA)** - Popayán
13. **Hidrológica de Nariño (HNA)** - Pasto

#### Región Orinoquía
14. **Hidrológica del Meta (HME)** - Villavicencio
15. **Hidrológica del Casanare (HCS)** - Yopal

#### Región Amazonía
16. **Hidrológica del Amazonas (HAM)** - Leticia

### Usuarios de Prueba

| Usuario | Contraseña | Rol | Descripción |
|---------|------------|-----|-------------|
| `admin_rector` | `admin123` | Admin Rector | Acceso completo al sistema |
| `supervisor_rector` | `admin123` | Admin Rector | Supervisión y reportes |
| `operador_atlantico` | `admin123` | Operador | Gestión Hidrológica Atlántico |
| `operador_bolivar` | `admin123` | Operador | Gestión Hidrológica Bolívar |
| `control_barranquilla` | `admin123` | Punto Control | Control QR Barranquilla |
| `control_cartagena` | `admin123` | Punto Control | Control QR Cartagena |

## Endpoints Principales

- **Admin Django**: http://localhost:8000/admin/
- **API Docs**: http://localhost:8000/api/docs/
- **API Schema**: http://localhost:8000/api/schema/
- **Auth API**: http://localhost:8000/api/v1/auth/
- **Inventory API**: http://localhost:8000/api/v1/inventory/
- **Transfers API**: http://localhost:8000/api/v1/transfers/
- **Notifications API**: http://localhost:8000/api/v1/notifications/

## Verificación del Sistema

### 1. Verificar Datos Iniciales

```bash
# Contar entidades creadas
python manage.py shell -c "
from apps.core.models import *
from apps.inventory.models import *
from django.contrib.auth import get_user_model

User = get_user_model()

print(f'Ente Rector: {EnteRector.objects.count()}')
print(f'Hidrológicas: {Hidrologica.objects.count()}')
print(f'Acueductos: {Acueducto.objects.count()}')
print(f'Usuarios: {User.objects.count()}')
print(f'Ítems: {ItemInventario.objects.count()}')
"
```

### 2. Probar APIs

```bash
# Obtener token de autenticación
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin_rector", "password": "admin123"}'

# Usar token para acceder a APIs
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/inventory/items/
```

### 3. Verificar Notificaciones

```bash
# Probar sistema de notificaciones
python manage.py test_notifications --usuario admin_rector

# Ver estadísticas
python manage.py test_notifications
```

### 4. Verificar Historial

```bash
# Crear eventos de prueba y ver historial
python manage.py test_historial --crear-eventos --mostrar-reporte

# Ver estadísticas generales
python manage.py test_historial
```

## Solución de Problemas

### Error de Conexión a Base de Datos

```bash
# Verificar que PostgreSQL esté ejecutándose
docker-compose ps

# Ver logs de la base de datos
docker-compose logs db

# Recrear base de datos
docker-compose down -v
docker-compose up -d db
docker-compose run --rm web python manage.py migrate
```

### Error de Redis

```bash
# Verificar Redis
docker-compose logs redis

# Probar conexión
docker-compose exec redis redis-cli ping
```

### Problemas con Migraciones

```bash
# Resetear migraciones (CUIDADO: elimina datos)
docker-compose run --rm web python manage.py migrate --fake-initial

# O recrear completamente
docker-compose down -v
docker-compose up -d db redis
docker-compose run --rm web python manage.py migrate
docker-compose run --rm web python manage.py bootstrap_system
```

### Logs y Debugging

```bash
# Ver logs en tiempo real
docker-compose logs -f web

# Acceder al shell de Django
docker-compose exec web python manage.py shell

# Ejecutar tests
docker-compose run --rm web python manage.py test
```

## Configuración de Producción

### Variables de Entorno Importantes

```bash
# Seguridad
SECRET_KEY=<clave-secreta-fuerte>
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Base de datos
DB_HOST=<host-produccion>
DB_NAME=<nombre-bd-produccion>
DB_USER=<usuario-bd>
DB_PASSWORD=<password-seguro>

# Redis
REDIS_URL=redis://<host-redis>:6379/0

# Email (para notificaciones)
EMAIL_HOST=<smtp-host>
EMAIL_PORT=587
EMAIL_HOST_USER=<email-usuario>
EMAIL_HOST_PASSWORD=<email-password>
```

### Comandos de Producción

```bash
# Recopilar archivos estáticos
python manage.py collectstatic --noinput

# Ejecutar con Gunicorn
gunicorn inventory_platform.wsgi:application

# Ejecutar Celery en producción
celery -A inventory_platform worker -D
celery -A inventory_platform beat -D
```

## Mantenimiento

### Tareas Programadas

El sistema incluye tareas automáticas de Celery:

- **Limpieza de notificaciones expiradas**: Diaria a las 2:00 AM
- **Limpieza de notificaciones antiguas**: Semanal los domingos a las 3:00 AM
- **Reporte mensual de notificaciones**: Primer día del mes a las 4:00 AM
- **Resumen diario**: Diario a las 8:00 AM

### Respaldos

```bash
# Respaldar base de datos
docker-compose exec db pg_dump -U postgres inventory_db > backup.sql

# Restaurar base de datos
docker-compose exec -T db psql -U postgres inventory_db < backup.sql
```

## Soporte

Para soporte técnico o preguntas sobre la configuración, consulte:

1. La documentación de la API en `/api/docs/`
2. Los logs del sistema
3. Los comandos de diagnóstico incluidos
4. El código fuente en el repositorio

---

**Nota**: Recuerde cambiar todas las contraseñas por defecto antes de usar en producción.