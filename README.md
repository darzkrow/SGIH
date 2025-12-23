# Plataforma de Gestión de Inventario

Sistema integral para el control de inventario de 16 Hidrológicas autónomas coordinadas por un Ente Rector.

## Características

- **Multitenencia**: Aislamiento de datos entre hidrológicas
- **Trazabilidad completa**: Ficha de vida para cada activo
- **Workflow de transferencias**: Con órdenes de traspaso digitales y códigos QR
- **Procesamiento asíncrono**: Generación de PDFs y notificaciones en tiempo real
- **Arquitectura contenedorizada**: Docker Compose completo

## Tecnologías

- **Backend**: Django 4.2 + Django REST Framework
- **Base de datos**: PostgreSQL 15
- **Cache/Broker**: Redis 7
- **Procesamiento asíncrono**: Celery
- **Contenedores**: Docker + Docker Compose
- **Proxy**: Nginx

## Instalación y Configuración

### Prerrequisitos

- Docker y Docker Compose
- Git

### Configuración inicial

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd inventory-platform
   ```

2. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

3. **Construir y levantar servicios**
   ```bash
   make build
   make up
   ```

4. **Ejecutar migraciones**
   ```bash
   make migrate
   ```

5. **Crear superusuario**
   ```bash
   make superuser
   ```

6. **Cargar datos iniciales**
   ```bash
   docker-compose -f docker-compose.dev.yml exec web python manage.py loaddata initial_data
   ```

## Comandos útiles

```bash
# Ver logs
make logs

# Ejecutar tests
make test

# Abrir shell de Django
make shell

# Crear migraciones
make makemigrations

# Detener servicios
make down
```

## Estructura del proyecto

```
inventory-platform/
├── apps/
│   ├── core/           # Autenticación, multitenencia
│   ├── inventory/      # Gestión de inventario
│   ├── transfers/      # Transferencias y QR
│   └── notifications/  # Notificaciones
├── inventory_platform/ # Configuración Django
├── docker-compose.yml  # Producción
├── docker-compose.dev.yml # Desarrollo
└── requirements.txt
```

## API Documentation

Una vez levantado el proyecto, la documentación de la API está disponible en:
- Swagger UI: http://localhost:8000/api/docs/
- Schema OpenAPI: http://localhost:8000/api/schema/

## Desarrollo

### Agregar nuevas funcionalidades

1. Crear modelos en la app correspondiente
2. Generar migraciones: `make makemigrations`
3. Aplicar migraciones: `make migrate`
4. Crear serializers y viewsets
5. Agregar URLs
6. Escribir tests

### Testing

```bash
# Ejecutar todos los tests
make test

# Tests específicos
docker-compose -f docker-compose.dev.yml exec web python manage.py test apps.inventory

# Tests con coverage
docker-compose -f docker-compose.dev.yml exec web coverage run --source='.' manage.py test
docker-compose -f docker-compose.dev.yml exec web coverage report
```

## Producción

Para desplegar en producción:

1. Configurar variables de entorno de producción
2. Usar `docker-compose.yml` (no el .dev.yml)
3. Configurar certificados SSL
4. Configurar backup de base de datos

```bash
make prod-build
make prod-up
```

## Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request